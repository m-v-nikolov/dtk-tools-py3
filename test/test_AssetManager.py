import os
import unittest

from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser

from COMPS.Data.QueryCriteria import QueryCriteria as COMPSQueryCriteria
from COMPS.Data.AssetCollection import AssetCollection as COMPSAssetCollection
from COMPS.Data.AssetCollectionFile import AssetCollectionFile as COMPSAssetCollectionFile

from simtools.Utilities.COMPSUtilities import get_experiment_by_id, COMPS_login
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.utils.reports.CustomReport import BaseReport
from dtk.vector.study_sites import configure_site
from simtools.AssetManager.AssetCollection import AssetCollection
from simtools.AssetManager.FileList import FileList
from simtools.AssetManager.SimulationAssets import SimulationAssets

class TestSimulationAssets(unittest.TestCase):

    SELECTED_BLOCK = 'SimulationAssets'

    def setUp(self):
        SetupParser.init(selected_block=self.SELECTED_BLOCK)
        self.config_builder = DTKConfigBuilder.from_defaults('VECTOR_SIM')
        configure_site(self.config_builder, 'Namawala')
        self.config_builder.add_reports(BaseReport(type="VectorHabitatReport"))

    def tearDown(self):
        SetupParser._uninit()

    def test_ambiguous_assets_assembly(self):
        # all missing
        kwargs = {'config_builder': self.config_builder}
        self.assertRaises(SimulationAssets.AmbiguousAssetSpecification, SimulationAssets.assemble_assets, **kwargs)

        #
        # missing item in base_collection_id
        base_collection_id = {
            SimulationAssets.COLLECTION_TYPES[0]: 'abc',
            SimulationAssets.COLLECTION_TYPES[1]: 'def',
            # missing a collection type here
        }
        use_local_files = dict([ [i, True] for i in SimulationAssets.COLLECTION_TYPES ])
        use_local_files[SimulationAssets.COLLECTION_TYPES[2]] = None
        kwargs = {
            'config_builder': self.config_builder,
            'base_collection_id': base_collection_id,
            'use_local_files': use_local_files
        }
        self.assertRaises(SimulationAssets.AmbiguousAssetSpecification, SimulationAssets.assemble_assets, **kwargs)

        #
        # missing item in use_local_files
        base_collection_id = dict([ [i, 'abc'] for i in SimulationAssets.COLLECTION_TYPES ])
        base_collection_id[SimulationAssets.COLLECTION_TYPES[2]] = None
        use_local_files = {
            SimulationAssets.COLLECTION_TYPES[0]: True,
            SimulationAssets.COLLECTION_TYPES[1]: True,
            # missing a collection type here
        }
        kwargs = {
            'config_builder': self.config_builder,
            'base_collection_id': base_collection_id,
            'use_local_files': use_local_files
        }
        self.assertRaises(SimulationAssets.AmbiguousAssetSpecification, SimulationAssets.assemble_assets, **kwargs)

    def test_proper_files_gathered(self):
        """
        A simple regression test to help make sure a garden path file detection/gathering process doesn't change.
        """
        regressions = {
            SimulationAssets.EXE: {
                'relative_path': '',
                'files': [
                    'Eradication.exe'
                ]
            },
            SimulationAssets.DLL: {
                'relative_path': 'reporter_plugins',
                'files': [
                    'libvectorhabitat_report_plugin.dll'

                ]
            },
            SimulationAssets.INPUT: {
                'relative_path': 'Namawala',
                'files': [
                    'Namawala_single_node_air_temperature_daily.bin',
                    'Namawala_single_node_air_temperature_daily.bin.json',
                    'Namawala_single_node_demographics.compiled.json',
                    'Namawala_single_node_land_temperature_daily.bin',
                    'Namawala_single_node_land_temperature_daily.bin.json',
                    'Namawala_single_node_rainfall_daily.bin',
                    'Namawala_single_node_rainfall_daily.bin.json',
                    'Namawala_single_node_relative_humidity_daily.bin',
                    'Namawala_single_node_relative_humidity_daily.bin.json'
                ]
            }
        }
        for collection_type in SimulationAssets.COLLECTION_TYPES:
            expected = regressions[collection_type]
            expected_files = sorted([ os.path.join(expected['relative_path'], file) for file in expected['files'] ])
            file_list = sorted(SimulationAssets._gather_files(self.config_builder, collection_type).files)
            self.assertEqual(len(file_list),    len(expected_files))
            self.assertEqual(sorted(file_list), sorted(expected_files))

    def test_prepare_existing_master_collection(self):
        """
        A regression test to verify we get back the same collection id for the same selected files.
        """
        expected_collection_id = 'e0ce1817-dc4a-e711-80c1-f0921c167860'

        use_local_files = {
            SimulationAssets.EXE: True,
            SimulationAssets.DLL: True,
            SimulationAssets.INPUT: True
        }
        base_collection_id = {
            SimulationAssets.EXE: None,
            SimulationAssets.DLL: None,
            SimulationAssets.INPUT: None
        }
        assets = SimulationAssets.assemble_assets(config_builder=self.config_builder,
                                                  base_collection_id=base_collection_id,
                                                  use_local_files=use_local_files)
        assets.prepare(location='HPC')
        self.assertEqual(str(assets.collection_id), expected_collection_id)

    def test_verify_asset_collection_id_and_tags_added_to_experiment(self):
        """
        Makes sure the individual asset collection ids are stored as tags on an experiment and that
        the 'master' asset collection id (id for all asset files together in one collection) is stored properly
        on the experiment as well.
        """
        from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory

        expected_asset_collection = 'e0ce1817-dc4a-e711-80c1-f0921c167860' # master collection

        run_sim_args = {'exp_name': 'AssetCollectionTestSim'}
        exp_manager = ExperimentManagerFactory.from_setup(config_builder=self.config_builder)
        exp_manager.run_simulations(**run_sim_args)

        # now query COMPS for this experiment and retrieve/verify tags
        exp_comps = get_experiment_by_id(exp_id=exp_manager.experiment.exp_id,
                                         query_criteria=COMPSQueryCriteria().select_children(children=['tags', 'configuration']))
        tags = exp_comps.tags
        for asset_type in SimulationAssets.COLLECTION_TYPES:
            tag = unicode(asset_type + '_collection_id')
            self.assertTrue(exp_manager.assets.collections.get(asset_type, None) is not None)
            self.assertTrue(tags.get(tag, None) is not None)
            self.assertEqual(str(exp_manager.assets.collections[asset_type].collection_id),
                             str(tags[tag]))
        self.assertEqual(len(tags), len(SimulationAssets.COLLECTION_TYPES))

        # verify the asset_collection_id was added properly
        asset_collection_id = exp_comps.configuration.asset_collection_id
        self.assertEqual(str(asset_collection_id), expected_asset_collection)

    # BaseExperimentManager tests below (move to different test file?)

    def test_verify_missing_files_properly_detected_and_reported(self):
        # using local files
        original_block = SetupParser.selected_block
        try:
            SetupParser.override_block(block='USE_LOCAL_FILES')
            exp_manager = ExperimentManagerFactory.from_setup(config_builder=self.config_builder)
            missing_files = exp_manager._detect_missing_files()
            self.assertEqual(len(missing_files), 0)

            # now add a spurious file that does not exist
            new_file = COMPSAssetCollectionFile(file_name='somefile.txt', relative_path='hello')
            new_file.root = "totallyMadeUp"
            new_file.is_local = True
            key = exp_manager.assets.collections.keys()[0]
            exp_manager.assets.collections[key].asset_files_to_use.append(new_file)
            missing_files = exp_manager._detect_missing_files()

            self.assertEqual(len(missing_files), 1)
            self.assertEqual(missing_files[0], os.path.join(new_file.root, new_file.relative_path, new_file.file_name))
        finally:
            SetupParser.override_block(block=original_block)

#    def test_get_commandline_works_properly(self):
#        raise Exception("undefined")

class TestAssetCollection(unittest.TestCase):
    LOCAL_ONLY = 'LOCAL_ONLY'
    REMOTE_ONLY = 'REMOTE_ONLY'
    EXISTING_COLLECTION_ID = '2129c37c-324a-e711-80c1-f0921c167860'
    INPUT_DIR = os.path.join(os.path.dirname(__file__), 'input', 'AssetCollection')
    SELECTED_BLOCK = 'AssetCollection'

    def setUp(self):
        SetupParser.init(selected_block=self.SELECTED_BLOCK)
        COMPS_login(SetupParser.get('server_endpoint'))

        self.existing_collection = AssetCollection(base_collection_id=self.EXISTING_COLLECTION_ID)
        self.existing_collection.prepare(location='HPC')
        self.existing_COMPS_asset_files = self.existing_collection.asset_files_to_use

        # a FileList object
        dir = os.path.join(self.INPUT_DIR, 'files')
        files = [ os.path.join(dir, f) for f in os.listdir(dir) ]
        root = os.path.dirname(os.path.dirname(files[0]))
        files = [ os.path.join(os.path.split(os.path.dirname(f))[1], os.path.basename(f)) for f in files ]
        self.local_files = FileList(root=root, files_in_root=files)

        # take one away
        files = list(self.local_files.files) # copy
        files.remove(os.path.join('files', 'file1_REMOTE_ONLY'))
        # add some more
        dir = os.path.join(self.INPUT_DIR, 'additional_files')
        additional_files = [os.path.join(dir, f) for f in os.listdir(dir)]
        additional_files = [ os.path.join(os.path.split(os.path.dirname(f))[1], os.path.basename(f)) for f in additional_files ]
        files += additional_files
        self.local_files_plus_minus = FileList(root=root, files_in_root=files)

    def tearDown(self):
        SetupParser._uninit()

    def test_file_invalid_configurations(self):
        kwargs = {}
        self.assertRaises(AssetCollection.InvalidConfiguration, AssetCollection, **kwargs)

        kwargs = {'base_collection_id': 'abc', 'remote_files': 'def'}
        self.assertRaises(AssetCollection.InvalidConfiguration, AssetCollection, **kwargs)

    def test_can_handle_empty_collections(self):
        """
        Tests if an empty file list causes problems (should not)
        """
        files = FileList(root='abc', files_in_root=[])

        collection = AssetCollection(local_files=files)
        self.assertEqual(len(collection.asset_files_to_use), 0)

        collection.prepare(location='LOCAL')
        self.assertEqual(collection.collection_id, 'LOCAL')

        collection.prepared = False
        collection.prepare(location='HPC')
        self.assertEqual(collection.collection_id, None)

    def test_properly_label_local_and_remote_files_and_verify_file_data(self):
        """
        This tests whether the code properly recognizes local/remote file usage (and precedence during conflicts)
        as well as verifies local vs. COMPS AssetCollection files via file count and md5.
        :return:
        """
        # all files are remote/in an existing asset collection
        new_collection = AssetCollection(base_collection_id=self.existing_collection.collection_id)
        for f in new_collection.asset_files_to_use:
            self.assertTrue(hasattr(f, 'is_local'))
            self.assertEqual(f.is_local, False)

        # all files remote, not necessarily in an existing asset collection
        new_collection = AssetCollection(remote_files=self.existing_COMPS_asset_files)
        for f in new_collection.asset_files_to_use:
            self.assertTrue(hasattr(f, 'is_local'))
            self.assertEqual(f.is_local, False)

        # all files are local
        new_collection = AssetCollection(base_collection_id=None, local_files=self.local_files)
        for f in new_collection.asset_files_to_use:
            self.assertTrue(hasattr(f, 'is_local'))
            self.assertEqual(f.is_local, True)

        # mix of local and existing remote files in a COMPS AssetCollection.
        # local_files should be preferred in case of conflicts
        new_collection = AssetCollection(base_collection_id=self.existing_collection.collection_id,
                                         local_files=self.local_files_plus_minus)
        for f in new_collection.asset_files_to_use:
            self.assertTrue(hasattr(f, 'is_local'))
            if self.REMOTE_ONLY in f.file_name: # we removed this file from self.local_files_pluS_minus, so it is remote only now.
                self.assertEqual(f.is_local, False)
            elif self.LOCAL_ONLY in f.file_name:
                self.assertEqual(f.is_local, True)
            else:
                self.assertEqual(f.is_local, True)

        # finally, verify that the resultant remote COMPSAssetCollection has the same files + MD5s of the files we requested.
        new_collection.prepare(location='HPC')
        remote_asset_files = COMPSAssetCollection.get(id=new_collection.collection_id,
                                                      query_criteria=AssetCollection.asset_files_query()).assets
        new_asset_files    = sorted(new_collection.asset_files_to_use, key = lambda x: x.file_name)
        remote_asset_files = sorted(remote_asset_files,                key = lambda x: x.file_name)

        self.assertEqual(len(new_collection.asset_files_to_use), len(remote_asset_files))
        for i in range(0,len(new_asset_files)):
            self.assertEqual(new_asset_files[i].file_name,     remote_asset_files[i].file_name)
            self.assertEqual(new_asset_files[i].relative_path, remote_asset_files[i].relative_path)
            self.assertEqual(new_asset_files[i].md5_checksum,  remote_asset_files[i].md5_checksum)

    def test_prepare_existing_collection(self):
        self.existing_collection.prepare(location='HPC')
        self.assertTrue(self.existing_collection.prepared)
        self.assertEqual(str(self.existing_collection.collection_id), self.EXISTING_COLLECTION_ID)

    def test_prepare_new_collection(self):
        import tempfile
        import random
        with tempfile.NamedTemporaryFile(mode='w+') as new_file:
            new_file.write('hello world! %s' % random.random())
            asset_file = COMPSAssetCollectionFile(file_name=os.path.basename(new_file.name), relative_path='.')

            self.existing_collection.asset_files_to_use.append(asset_file)
            self.existing_collection.prepare(location='HPC')

            self.assertTrue(self.existing_collection.prepared)
            self.assertTrue(self.existing_collection.collection_id is not None)
            self.assertTrue(self.existing_collection.collection_id != self.EXISTING_COLLECTION_ID) # a new collection

if __name__ == '__main__':
    unittest.main()
