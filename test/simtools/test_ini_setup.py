import os
import stat
import unittest

from simtools.DataAccess.DataStore import DataStore
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.ModBuilder import ModBuilder, SingleSimulationBuilder, RunNumberSweepBuilder, ModFn
from simtools.SetupParser import SetupParser
from simtools.SimConfigBuilder import SimConfigBuilder, PythonConfigBuilder
from simtools.Utilities.General import get_md5, CommandlineGenerator
from COMPS.Data.Simulation import SimulationState


class TestSetupParser(unittest.TestCase):

    def setUp(self):
        self.cwd = os.getcwd()
        self.input_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'input')

    def tearDown(self):
        os.chdir(self.cwd)
        SetupParser._uninit()

    def test_reinitialization_not_allowed(self):
        SetupParser.init(selected_block="LOCAL")
        kwargs = {"selected_block": "LOCAL"}
        self.assertRaises(SetupParser.AlreadyInitialized, SetupParser.init, **kwargs)

        #SetupParser.init(**kwargs)

    def test_overlay_selection_priority(self):
        # Test all combinations of provided ini X commissioning ini X local dir ini
        local = ['local.ini', None]
        provided = ['provided.ini', None]
        commissioning = ['commissioning.ini', None]
        for l in local:
            for p in provided:
                for c in commissioning:
                    overlay_selection = SetupParser._select_overlay(local_file=l, provided_file=p, commissioning_file=c)
                    if p:
                        expected_overlay = p
                    elif l:
                        expected_overlay = l
                    elif c:
                        expected_overlay = c
                    else:
                        expected_overlay = None

                    self.assertEqual(overlay_selection, expected_overlay, "local: %s provided: %s commissioning: %s" %
                                     (l, p, c))

    def test_raises_if_no_default_ini_available(self):
        original_default = SetupParser.default_file
        try:
            SetupParser.default_file = "doesnotexist.ini"
            kwargs = {'selected_block': 'LOCAL'}
            self.assertRaises(SetupParser.MissingIniFile, SetupParser.init, **kwargs)
        finally:
            SetupParser.default_file = original_default

    def test_verify_user_in_default_block(self):
        SetupParser.init(selected_block='LOCAL')
        self.assertTrue('user' in SetupParser.singleton.setup.defaults().keys())
        self.assertNotEqual(SetupParser.singleton.setup.defaults()['user'], None)

    def test_raises_if_selected_block_not_available(self):
        kwargs = {'selected_block': 'NOTABLOCK'}
        self.assertRaises(SetupParser.MissingIniBlock, SetupParser.init, **kwargs)

    def test_verify_block_selection(self):
        SetupParser.init(selected_block='LOCAL')
        self.assertEqual(SetupParser.selected_block, 'LOCAL')

    def test_verify_override_block(self):
        """
        1) set the SetupParser once to get the expected value, unset it, then 2) load a
        different selected block & then override it to the first. Should get same answer
        both routes.
        """
        SetupParser.init(selected_block='LOCAL', is_testing=True)
        expected_params = dict(SetupParser.items(SetupParser.selected_block))
        SetupParser._uninit()
        SetupParser.init(selected_block='HPC', is_testing=True)
        SetupParser.override_block('LOCAL')
        override_params = dict(SetupParser.items(SetupParser.selected_block))
        self.assertEqual(override_params, expected_params)

    def test_no_overlay_default_block(self):
        SetupParser.init()
        self.assertEqual(SetupParser.selected_block, 'LOCAL')
        self.assertEqual(SetupParser.get('type'), 'LOCAL')

        # User should be there
        self.assertIsNotNone(SetupParser.get('user'))

        # We dont want HPC or unknown params
        self.assertRaises(ValueError, SetupParser.get, 'use_comps_asset_svc')
        self.assertRaises(ValueError, SetupParser.get, 'WRONG')

    def test_overlay_file_values(self):
        filename = os.path.join(self.input_path, SetupParser.ini_filename)
        SetupParser.init(selected_block='TEST', setup_file=filename, is_testing=True)

        # verify the selected block is correct
        self.assertEqual(SetupParser.selected_block, 'TEST')

        # data overlay - param in TEST, no conflict with DEFAULT or default ini (TEST wins)
        self.assertEqual(SetupParser.get('made_up_param'), '1')

        # data overlay - param in TEST, conflict with DEFAULT and default ini (TEST wins)
        self.assertEqual(SetupParser.get('environment'), 'TestEnv')

        # data overlay - DEFAULT conflict with default ini (DEFAULT wins)
        self.assertEqual(SetupParser.get('max_threads'), '0')

        # data overlay - only in default ini DEFAULT, (default ini DEFAULT wins, obviously!)
        self.assertIsNotNone(SetupParser.get('exe_path'))

    def test_has_option(self):
        filename = os.path.join(self.input_path, SetupParser.ini_filename)
        SetupParser.init(selected_block='TEST', setup_file=filename, is_testing=True)
        self.assertTrue(SetupParser.has_option('environment'))
        self.assertFalse(SetupParser.has_option('notanoption'))

    def test_items(self):
        filename = os.path.join(self.input_path, SetupParser.ini_filename)
        SetupParser.init(selected_block='TEST', setup_file=filename, is_testing=True)
        self.assertEqual(len(SetupParser.items()), 24)
        self.assertEqual(len(SetupParser.items(block='HPC')), 20)

    def test_get(self):
        filename = os.path.join(self.input_path, SetupParser.ini_filename)
        SetupParser.init(selected_block='TEST', setup_file=filename, is_testing=True)
        default_value = 'abcdefg'

        # param present and default value not used
        kwargs = {'parameter': 'made_up_param', 'default': default_value}
        self.assertEqual(SetupParser.get(**kwargs), '1')

        # param not present and no default provided
        kwargs = {'parameter': 'notaparameter'}
        self.assertRaises(ValueError, SetupParser.get, **kwargs)

        # default value provided and used
        kwargs = {'parameter': 'notaparameter', 'default': default_value}
        test_value = SetupParser.get(**kwargs)
        self.assertEqual(test_value, default_value)

    def test_explicit_overrides(self):
        filename = os.path.join(self.input_path, SetupParser.ini_filename)
        overrides = {'in_all': 'yellow'}
        SetupParser.init(selected_block='TEST', setup_file=filename, overrides=overrides, is_testing=True)
        self.assertEqual(SetupParser.get('in_all'), overrides['in_all'])

        # verify this works even after block change
        SetupParser.override_block(block='LOCAL2')
        self.assertEqual(SetupParser.get('in_all'), overrides['in_all'])

    def test_get_boolean(self):
        filename = os.path.join(self.input_path, SetupParser.ini_filename)
        SetupParser.init(selected_block='TEST', setup_file=filename, is_testing=True)
        # assertIs checks if the items evaluate to the same object (not truthy comparison)
        self.assertIs(SetupParser.getboolean('this_is_true'), True)
        self.assertIs(SetupParser.getboolean('this_is_false'), False)
        kwargs = {'parameter': 'notaparameter'}
        self.assertRaises(ValueError, SetupParser.getboolean, **kwargs) # not present in TEST
        kwargs = {'parameter': 'environment'}
        self.assertRaises(ValueError, SetupParser.getboolean, **kwargs) # not a boolean, but is present in TEST.

    def test_fail_if_not_initialized(self):
        SetupParser._uninit() # just to make sure!
        args = [SetupParser, 'selected_block']
        self.assertRaises(SetupParser.NotInitialized, getattr, *args)
        kwargs = {'parameter': 'selected_block'}
        self.assertRaises(SetupParser.NotInitialized, SetupParser.get, **kwargs)

    def test_verify_uninit(self):
        self.assertFalse(SetupParser.initialized)
        SetupParser.init()
        self.assertTrue(SetupParser.initialized)
        SetupParser._uninit()
        self.assertFalse(SetupParser.initialized)
        self.assertEqual(SetupParser.singleton, None)

    def test_old_style_initialization(self):
        # verify that old style works! And as expected :)
        self.assertFalse(SetupParser.initialized)
        self.assertRaises(Exception, SetupParser) #SetupParser()
        #self.assertTrue(SetupParser.initialized)
        SetupParser('LOCAL')
        self.assertTrue (hasattr(SetupParser, 'selected_block'))
        self.assertEqual(getattr(SetupParser, 'selected_block'), 'LOCAL')
        self.assertEqual(SetupParser.get('max_threads'), '16')

        SetupParser._uninit()
        self.assertFalse(SetupParser.initialized)
        SetupParser('HPC', is_testing=True)
        self.assertTrue(SetupParser.initialized)
        self.assertEqual(SetupParser.selected_block, 'HPC')

        # test silent override of specified block to support legacy usage
        SetupParser('HPC', is_testing=True)
        self.assertEqual(SetupParser.selected_block, 'HPC')
        SetupParser('LOCAL')
        self.assertEqual(SetupParser.selected_block, 'LOCAL')


    def test_init_with_singleton_provided(self):
        """
        This is covering the case where we call (in a new process): SetupParser(singleton=some_object)
        :return:
        """
        attr = 'johns_favorite_color' # an attribute NOT in the ini file to make sure we keep any set values
        value = 'purple'
        SetupParser('LOCAL')
        SetupParser.singleton.setup.set('LOCAL', attr, value)
        singleton = SetupParser.singleton
        SetupParser._uninit()
        SetupParser.init(singleton=singleton)
        self.assertEqual(SetupParser.get(attr), value)

if __name__ == '__main__':
    unittest.main()
