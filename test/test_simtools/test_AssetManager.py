import os
import unittest
from ConfigParser import ConfigParser

from COMPS.Data.AssetCollectionFile import AssetCollectionFile as COMPSAssetCollectionFile
from COMPS.Data.QueryCriteria import QueryCriteria as COMPSQueryCriteria

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.utils.reports.CustomReport import BaseReport
from dtk.vector.study_sites import configure_site
from simtools.AssetManager.AssetCollection import AssetCollection
from simtools.AssetManager.FileList import FileList
from simtools.AssetManager.SimulationAssets import SimulationAssets
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser
from simtools.Utilities.COMPSUtilities import COMPS_login, get_asset_collection, \
    get_asset_collection_by_tag


class TestSimulationAssets(unittest.TestCase):

    SELECTED_BLOCK = 'SimulationAssets'

    def setUp(self):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        input_dir = os.path.join(current_dir, 'input')
        self.am_simtools = os.path.join(input_dir, 'am_simtools.ini')

        # Adjust path sensitive parameters in the ini file
        cp = ConfigParser()
        cp.read(self.am_simtools)
        cp.set('DEFAULT', 'path', input_dir)
        cp.set('DEFAULT', 'example_dir', os.path.join(current_dir, '..', '..', 'examples'))
        cp.write(open(self.am_simtools, 'w'))

        SetupParser.init(selected_block=self.SELECTED_BLOCK, setup_file=self.am_simtools)
        self.config_builder = DTKConfigBuilder.from_defaults('VECTOR_SIM')
        configure_site(self.config_builder, 'Namawala')
        self.config_builder.add_reports(BaseReport(type="VectorHabitatReport"))

    def tearDown(self):
        SetupParser._uninit()
        # Revert path sensitive parameters in the ini file
        cp = ConfigParser()
        cp.read(self.am_simtools)
        cp.set('DEFAULT', 'path', '')
        cp.set('DEFAULT', 'example_dir', '')
        cp.write(open(self.am_simtools, 'w'))

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
        sa = SimulationAssets()
        for collection_type in SimulationAssets.COLLECTION_TYPES:
            expected = regressions[collection_type]
            expected_files = sorted([ os.path.join(expected['relative_path'], file) for file in expected['files'] ])
            file_list = sorted(sa._gather_files(self.config_builder, collection_type).files)
            self.assertEqual(len(file_list),    len(expected_files))
            self.assertEqual(sorted([os.path.join(f.relative_path, f.file_name) for f in file_list]), sorted(expected_files))

    def test_prepare_existing_master_collection(self):
        """
        A regression test to verify we get back the same collection id for the same selected files.
        """
        expected_collection_id = '786f0e24-c64b-e711-80c1-f0921c167860'
        assets = SimulationAssets()
        assets.prepare(self.config_builder)
        self.assertEqual(str(assets.collection_id), expected_collection_id)

    def test_verify_asset_collection_id_and_tags_added_to_experiment(self):
        """
        Makes sure the individual asset collection ids are stored as tags on an experiment and that
        the 'master' asset collection id (id for all asset files together in one collection) is stored properly
        on the simulations as well.
        """
        expected_asset_collection = '786f0e24-c64b-e711-80c1-f0921c167860' # master collection

        run_sim_args = {'exp_name': 'AssetCollectionTestSim'}
        exp_manager = ExperimentManagerFactory.from_cb(config_builder=self.config_builder)
        exp_manager.run_simulations(**run_sim_args)

        # now query COMPS for this experiment and retrieve/verify tags
        sim = exp_manager.comps_experiment.get_simulations(query_criteria=COMPSQueryCriteria().select_children(children=['tags', 'configuration']))[0]
        tags = sim.tags
        for asset_type in SimulationAssets.COLLECTION_TYPES:
            tag = "%s_collection_id" % asset_type
            self.assertTrue(exp_manager.assets.collections.get(asset_type, None) is not None)
            self.assertTrue(tags.get(tag, None) is not None)

        # verify the asset_collection_id was added properly
        asset_collection_id = sim.configuration.asset_collection_id
        self.assertEqual(str(asset_collection_id), expected_asset_collection)

class TestAssetCollection(unittest.TestCase):
    LOCAL_ONLY = 'LOCAL_ONLY'
    REMOTE_ONLY = 'REMOTE_ONLY'
    EXISTING_COLLECTION_ID = '2129c37c-324a-e711-80c1-f0921c167860'
    INPUT_DIR = os.path.join(os.path.dirname(__file__), 'input', 'AssetCollection')
    SELECTED_BLOCK = 'AssetCollection'

    def setUp(self):
        SetupParser._uninit()
        current_dir = os.path.dirname(os.path.realpath(__file__))
        SetupParser.init(selected_block=self.SELECTED_BLOCK,
                         setup_file=os.path.join(current_dir, 'input', 'am_simtools.ini'))
        COMPS_login(SetupParser.get('server_endpoint'))

        self.existing_collection = AssetCollection(base_collection=get_asset_collection(self.EXISTING_COLLECTION_ID))
        self.existing_collection.prepare(location='HPC')
        self.existing_COMPS_asset_files = self.existing_collection.asset_files_to_use

        # a FileList object
        dir = os.path.join(self.INPUT_DIR, 'files')
        files = [ os.path.join(dir, f) for f in os.listdir(dir) ]
        root = os.path.dirname(os.path.dirname(files[0]))
        files = [ os.path.join(os.path.split(os.path.dirname(f))[1], os.path.basename(f)) for f in files ]
        self.local_files = FileList(root=root, files_in_root=files)

        # take one away
        files = [os.path.join(f.relative_path, f.file_name) for f in self.local_files.files if f.file_name != 'file1_REMOTE_ONLY']
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

        kwargs = {'base_collection': 'abc', 'remote_files': 'def'}
        self.assertRaises(AssetCollection.InvalidConfiguration, AssetCollection, **kwargs)

    def test_can_handle_empty_collections(self):
        """
        Tests if an empty file list causes problems (should not)
        """
        files = FileList(root=os.getcwd(), files_in_root=[])

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
        new_collection = AssetCollection(base_collection=get_asset_collection(self.existing_collection.collection_id))
        for f in new_collection.asset_files_to_use:
            self.assertTrue(hasattr(f, 'is_local'))
            self.assertEqual(f.is_local, False)

        # all files remote, not necessarily in an existing asset collection
        new_collection = AssetCollection(remote_files=self.existing_COMPS_asset_files)
        for f in new_collection.asset_files_to_use:
            self.assertTrue(hasattr(f, 'is_local'))
            self.assertEqual(f.is_local, False)

        # all files are local
        new_collection = AssetCollection(base_collection=None, local_files=self.local_files)
        for f in new_collection.asset_files_to_use:
            self.assertTrue(hasattr(f, 'is_local'))
            self.assertEqual(f.is_local, True)

        # mix of local and existing remote files in a COMPS AssetCollection.
        # local_files should be preferred in case of conflicts
        new_collection = AssetCollection(base_collection=get_asset_collection(self.existing_collection.collection_id),
                                         local_files=self.local_files_plus_minus)
        for f in new_collection.asset_files_to_use:
            self.assertTrue(hasattr(f, 'is_local'))
            if self.REMOTE_ONLY in f.file_name: # we removed this file from self.local_files_pluS_minus, so it is remote only now.
                self.assertEqual(f.is_local, False)
            elif self.LOCAL_ONLY in f.file_name:
                self.assertEqual(f.is_local, True)

        # finally, verify that the resultant remote COMPSAssetCollection has the same files + MD5s of the files we requested.
        new_collection.prepare(location='HPC')
        remote_asset_files = get_asset_collection(new_collection.collection_id).assets
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

    DEFAULT_COLLECTION_NAME = 'EMOD 2.10'
    DEFAULT_COLLECTION_ID = 'c2d9468d-2b4a-e711-80c1-f0921c167860'

    def test_asset_collection_id_for_tag(self):
        tag_name = 'Name'
        asset_collections = [
            { # single match case
                'Name': self.DEFAULT_COLLECTION_NAME,
                'id': self.DEFAULT_COLLECTION_ID
            },
            { # 0 match case
                'Name': 'To be, or not to be: that is the question',
                'id': None
            },
            { # multiple match case
                'Name': 'EMOD',
                'id': None
            }
        ]
        for collection in asset_collections:
            key_tag = 'Name'
            c = get_asset_collection_by_tag(tag_name=key_tag, tag_value=collection[key_tag])
            id = c.id if c else None
            id = str(id) if id else id # convert UUID to string if not None
            self.assertEqual(id, collection['id'])

    # This verifies that a well-known default collection name is converted to the expected asset collection id
    def test_default_collection_usage_properly_sets_the_AssetCollection(self):
        collection = AssetCollection(base_collection=get_asset_collection(self.DEFAULT_COLLECTION_NAME))
        self.assertEqual(str(collection.base_collection.id), self.DEFAULT_COLLECTION_ID)

if __name__ == '__main__':
    unittest.main()
