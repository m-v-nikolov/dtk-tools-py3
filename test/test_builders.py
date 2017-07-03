import logging
import os
import unittest

from calibtool.study_sites.set_calibration_site import set_calibration_site
from simtools.ModBuilder import ModBuilder, SingleSimulationBuilder, ModFn

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.utils.builders.sweep import RunNumberSweepBuilder, GenericSweepBuilder
from dtk.vector.study_sites import configure_site
from dtk.vector.species import get_species_param, set_species_param
from dtk.interventions.malaria_drugs import get_drug_param, set_drug_param

class TestBuilders(unittest.TestCase):

    def setUp(self):
        ModBuilder.metadata = {}  # ModList constructor resets this in base class
        self.cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')
        self.input_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'input')

    def tearDown(self):
        pass

    def test_param_fn(self):
        k, v = ('Simulation_Duration', 100)
        fn = ModFn(DTKConfigBuilder.set_param, k, v)
        fn(self.cb)
        logging.debug('Parameter %s has value %s set from %s', k, self.cb.get_param(k), v)
        logging.debug('ModBuilder metadata: %s', ModBuilder.metadata)
        self.assertEqual(self.cb.get_param(k), v)
        self.assertEqual(ModBuilder.metadata, {k: v})

    def test_site_fn(self):
        s = 'Namawala'
        fn = ModFn(configure_site, s)
        fn(self.cb)
        logging.debug('Demographics_Filenames: %s', self.cb.get_param('Demographics_Filenames'))
        logging.debug('ModBuilder metadata: %s', ModBuilder.metadata)
        self.assertTrue('Namawala' in self.cb.get_param('Demographics_Filenames')[0])
        self.assertEqual(ModBuilder.metadata, {'_site_': 'Namawala', 'population_scale': 1})

    def test_calibsite_fn(self):
        from calibtool.study_sites.NamawalaCalibSite import NamawalaCalibSite
        s = NamawalaCalibSite()
        fn = ModFn(set_calibration_site, s)
        fn(self.cb)
        self.assertEqual(self.cb.campaign['Events'][0]['Event_Coordinator_Config']['Intervention_Config']['class'], 'InputEIR')
        self.assertEqual(self.cb.custom_reports[0].type, 'MalariaSummaryReport')
        self.assertEqual(ModBuilder.metadata, {'_site_': 'Namawala'})

    def test_custom_fn(self):
        v = [100, 50]
        fn = ModFn(set_species_param, 'gambiae', 'Required_Habitat_Factor', value=v)
        fn(self.cb)
        self.assertListEqual(get_species_param(self.cb, 'gambiae', 'Required_Habitat_Factor'), v)
        self.assertEqual(ModBuilder.metadata, {'gambiae.Required_Habitat_Factor': v})

    def test_default(self):
        b = SingleSimulationBuilder()
        ngenerated = 0
        for ml in b.mod_generator:
            self.assertEqual(ml, [])
            self.assertEqual(b.metadata, {})
            ngenerated += 1
        self.assertEqual(ngenerated, 1)

    def test_run_number(self):
        b = RunNumberSweepBuilder(nsims=10)
        ngenerated = 0
        for i, ml in enumerate(b.mod_generator):
            for m in ml:
                m(self.cb)
            self.assertEqual(b.metadata, {'Run_Number': i})
            self.assertEqual(self.cb.get_param('Run_Number'), i)
            ngenerated += 1
        self.assertEqual(ngenerated, 10)

    def test_generic_sweep(self):

        def verify(b):
            md = [(0.05, 100, 'Namawala'),
                  (0.05, 100, 'Matsari'),
                  (0.1, 100, 'Namawala'),
                  (0.1, 100, 'Matsari')]

            ngenerated = 0
            for i, ml in enumerate(b.mod_generator):
                for m in ml:
                    m(self.cb)
                mdd = dict(zip(('x_Temporary_Larval_Habitat', 'Simulation_Duration', '_site_'), md[i]))
                mdd.update({'population_scale': 1})
                self.assertEqual(b.metadata, mdd)
                self.assertEqual(self.cb.get_param('x_Temporary_Larval_Habitat'), md[i][0])
                ngenerated += 1
            self.assertEqual(ngenerated, 4)

        b = ModBuilder.from_combos([ModFn(DTKConfigBuilder.set_param, 'x_Temporary_Larval_Habitat', v) for v in [0.05,0.1]],
                                   [ModFn(DTKConfigBuilder.set_param, 'Simulation_Duration', 100)],
                                   [ModFn(configure_site, s) for s in ['Namawala','Matsari']])

        verify(b)

        b = GenericSweepBuilder.from_dict({'x_Temporary_Larval_Habitat': [0.05, 0.1],
                                           'Simulation_Duration': [100],
                                           '_site_': ['Namawala', 'Matsari']})

        verify(b)

    def test_multiple_site_exception(self):

        def verify(b):
            with self.assertRaises(ValueError):
                for ml in b.mod_generator:
                    pass

        b = ModBuilder.from_combos([ModFn(set_calibration_site, 'Matsari')],
                                   [ModFn(configure_site, 'Namawala')])
        verify(b)

        b = ModBuilder.from_combos([ModFn(configure_site, 'Matsari')],
                                   [ModFn(configure_site, 'Namawala')])
        verify(b)

        b = ModBuilder.from_combos([ModFn(set_calibration_site, 'Matsari')],
                                   [ModFn(set_calibration_site, 'Namawala')])
        verify(b)

    def test_vector_drug_param_sweep(self):
        b = ModBuilder.from_combos([ModFn(set_species_param, 'gambiae', 'Required_Habitat_Factor', value=v) for v in [(100, 50), (200, 100)]],
                                   [ModFn(set_drug_param, 'Artemether', 'Max_Drug_IRBC_Kill', value=v) for v in [4, 2]])
        md = [(4, (100, 50)),
              (2, (100, 50)),
              (4, (200, 100)),
              (2, (200, 100))]

        ngenerated=0
        for i, ml in enumerate(b.mod_generator):
            for m in ml:
                m(self.cb)
            self.assertListEqual([v for v in b.metadata.values()], list(md[i]))
            self.assertEqual(get_species_param(self.cb, 'gambiae', 'Required_Habitat_Factor'), md[i][1])
            self.assertEqual(get_drug_param(self.cb, 'Artemether', 'Max_Drug_IRBC_Kill'), md[i][0])
            ngenerated += 1
        self.assertEqual(ngenerated, 4)

    def test_listed_events(self):
        from simtools.SetupParser import SetupParser
        SetupParser.init()
        # Create a builder based on the files
        builder = DTKConfigBuilder.from_files(os.path.join(self.input_path,'customevents','configbad.json'),
                                              os.path.join(self.input_path,'customevents','campaign.json'))

        # Call the file writter
        def fake_write(name,content):
            return
        builder.file_writer(fake_write)

        # Try if the listed events worked
        self.assertEqual(set(builder.config['parameters']['Listed_Events']), set([
            "Received_ITN",
            "TestedPositive",
            "Received_Campaign_Drugs",
            "Received_Treatment",
            "Received_Test",
            "Received_Survey",
            "Diagnostic_Survey_5",
            "Give_Drugs"
        ]))

if __name__ == '__main__':
    unittest.main()
