import os
import stat
import unittest

from simtools import utils
from simtools.ExperimentManager import ExperimentManagerFactory
from simtools.ModBuilder import ModBuilder, SingleSimulationBuilder, RunNumberSweepBuilder
from simtools.SetupParser import SetupParser
from simtools.SimConfigBuilder import SimConfigBuilder, PythonConfigBuilder


class TestConfigBuilder(unittest.TestCase):

    def setUp(self):
        self.cb = SimConfigBuilder.from_defaults('DUMMY')
        self.setup = SetupParser()

    def test_kwargs(self):
        self.assertEqual(self.cb.get_param('Simulation_Type'), 'DUMMY')

    def test_set_param(self):
        self.cb.set_param('foo', 'bar')
        self.assertEqual(self.cb.get_param('foo'), 'bar')

    def test_update_params(self):
        self.cb.update_params(dict(foo='bar'))
        self.assertEqual(self.cb.get_param('foo'), 'bar')

    def test_copy(self):
        cb2 = SimConfigBuilder()
        cb2.copy_from(self.cb)
        self.assertEqual(self.cb.__dict__, cb2.__dict__)

    def test_dump_to_string(self):
        s = self.cb.dump_files_to_string()
        self.assertListEqual(s.keys(), ['config'])
        self.assertDictEqual(eval(s['config']), dict(Simulation_Type='DUMMY'))

    def test_dump_to_file(self):
        self.cb.dump_files(os.getcwd())
        self.assertTrue(os.path.exists('config.json'))
        os.remove('config.json')

    def test_stage_exe(self):
        local_setup = dict(self.setup.items())

        file1 = 'input/dummy_exe_folder/dummy_exe.txt'
        md5 = utils.get_md5(file1)
        self.cb.stage_executable(file1, local_setup)
        staged_dir = os.path.join(self.setup.get('bin_staging_root'), md5)
        staged_path = os.path.join(staged_dir, 'dummy_exe.txt')
        self.assertTrue(os.path.exists(staged_path))

        file2 = 'input/another_dummy_exe_folder/dummy_exe.txt'
        os.chmod(file2, stat.S_IREAD)  # This is not writeable, but should not error because it isn't copied
        another_md5 = utils.get_md5(file2)
        self.cb.stage_executable(file2, local_setup)
        self.assertEqual(md5, another_md5)

        self.cb.stage_executable('\\\\remote\\path\\to\\file.exe', local_setup)

        os.remove(staged_path)
        os.rmdir(staged_dir)

    def test_commandline(self):
        commandline = self.cb.get_commandline('input/file.txt', dict(self.setup.items()))
        self.assertEqual('input/file.txt', commandline.Commandline)

        another_command = utils.CommandlineGenerator('input/file.txt', {'--config': 'config.json'}, [])
        self.assertEqual('input/file.txt --config config.json', another_command.Commandline)


class TestConfigExceptions(unittest.TestCase):

    def test_bad_kwargs(self):
        self.assertRaises(Exception, lambda: SimConfigBuilder.from_defaults('DUMMY', Not_A_Climate_Parameter=26))

    def test_no_simtype(self):
        self.assertRaises(Exception, lambda: SimConfigBuilder.from_defaults())


class TestSetupParser(unittest.TestCase):

    def setUp(self):
        self.cwd = os.getcwd()
        SetupParser.selected_block = None
        SetupParser.setup_file = None

    def tearDown(self):
        os.chdir(self.cwd)
        SetupParser.selected_block = None
        SetupParser.setup_file = None

    def test_fallback(self):
        # Specified fallback
        sp = SetupParser(selected_block="BAD_BLOCK",fallback='HPC')
        self.assertEqual(sp.selected_block,'HPC')

        # Default LOCAL fallback
        SetupParser.selected_block = None
        SetupParser.setup_file = None
        sp = SetupParser(selected_block="BAD_BLOCK")
        self.assertEqual(sp.selected_block, 'LOCAL')

        # Fallback value coming from overlay
        os.chdir(os.path.abspath('input'))
        SetupParser.selected_block = None
        SetupParser.setup_file = None
        sp = SetupParser(selected_block="BAD_BLOCK", fallback="LOCAL2")
        self.assertEqual(sp.selected_block, 'LOCAL2')

        # Bad fallback
        SetupParser.selected_block = None
        SetupParser.setup_file = None
        sp = SetupParser(selected_block="BAD_BLOCK", fallback="BAD_FALLBACK")
        self.assertEqual(sp.selected_block, 'LOCAL')

    def test_no_overlay_default_block(self):
        sp = SetupParser()
        # Default should be LOCAL block
        self.assertEqual(sp.selected_block, 'LOCAL')
        self.assertEqual(sp.get('type'), 'LOCAL')

        # User should be there
        self.assertIsNotNone(sp.get('user'))

        # We dont want HPC or unknown params
        self.assertRaises(ValueError, sp.get, 'use_comps_asset_svc')
        self.assertRaises(ValueError, sp.get, 'WRONG')

    def test_block_selection(self):
        os.chdir(os.path.abspath('input'))
        # Pass a block name
        sp = SetupParser('HPC')
        self.assertEqual(sp.selected_block, 'HPC')
        self.assertEqual(sp.get('type'),'HPC')

        # Pass another block name but shouldn't change
        sp = SetupParser('TEST')
        self.assertEqual(sp.selected_block, 'HPC')

        # Change in the class and subsequent instances
        SetupParser.selected_block = None
        SetupParser.selected_block = 'TEST'
        sp = SetupParser('HPC')
        self.assertEqual('TEST', sp.selected_block)

        # And now force
        sp = SetupParser('HPC', force=True)
        self.assertEqual(sp.selected_block, 'HPC')

    def test_overlay_file_cwd(self):
        os.chdir(os.path.abspath('input'))
        sp = SetupParser('TEST')

        # We have the TEST selected
        self.assertEqual(sp.selected_block,'TEST')

        # The data overlay properly
        self.assertEqual(sp.get('use_comps_asset_svc'), str(1))

        # and the defaults are properly retrieved
        self.assertIsNotNone(sp.get('bin_staging_root'))
        self.assertIsNotNone(sp.get('compress_assets'))

        # But not all of them (we dont want LOCAL)
        self.assertRaises(ValueError, sp.get, 'max_local_sims')

        # Test if the default are overlayed from cwd file
        self.assertEqual(sp.get('max_threads'), str(0))

        # global file DEFAULT(max_threads = 16) / local file DEFAULT(max_threads = 0) / local file LOCAL2(max_threads = 1)
        SetupParser.selected_block = None
        sp = SetupParser('LOCAL2')
        self.assertEqual(sp.get('max_threads'), str(1))

    def test_overlay_file_with_path(self):
        sp = SetupParser('DUMMY','input/dummy_ini.ini')
        self.assertEqual(sp.get('max_threads'),str(1000))
        self.assertEqual(sp.get('type'),'LOCAL')



class TestBuilders(unittest.TestCase):

    def setUp(self):
        ModBuilder.metadata = {}
        self.cb = SimConfigBuilder.from_defaults('DUMMY')

    def test_param_fn(self):
        k, v = ('foo', 'bar')
        fn = ModBuilder.ModFn(SimConfigBuilder.set_param, k, v)
        fn(self.cb)
        self.assertEqual(self.cb.get_param('foo'), 'bar')
        self.assertDictEqual(ModBuilder.metadata, dict(foo='bar'))

    def test_default(self):
        b = SingleSimulationBuilder()
        ngenerated = 0
        for ml in b.mod_generator:
            self.assertEqual(ml, [])
            self.assertEqual(b.metadata, {})
            ngenerated += 1
        self.assertEqual(ngenerated, 1)

    def test_custom_fn(self):
        v = [100, 50]
        self.cb.set_param('nested', {'foo': {'bar': [0, 0]}})

        def custom_fn(cb, foo, bar, value):
            cb.config['nested'][foo][bar] = value
            return {'.'.join([foo, bar]): value}

        fn = ModBuilder.ModFn(custom_fn, 'foo', 'bar', value=v)
        fn(self.cb)
        self.assertListEqual(self.cb.get_param('nested')['foo']['bar'], v)
        self.assertEqual(ModBuilder.metadata, {'foo.bar': v})


class TestLocalExperimentManagerCreate(unittest.TestCase):

    def test_create(self):
        model_file = 'input/dummy_model.py'
        local_manager = ExperimentManagerFactory.from_model(model_file, 'LOCAL')
        local_manager.create_simulations(config_builder=PythonConfigBuilder.from_defaults('sleep'))


class TestLocalExperimentManager(unittest.TestCase):

    nsims = 3

    def test_run(self):
        model_file = 'input/dummy_model.py'
        local_manager = ExperimentManagerFactory.from_model(model_file, 'LOCAL')
        local_manager.run_simulations(config_builder=PythonConfigBuilder.from_defaults('sleep'),
                                      exp_builder=RunNumberSweepBuilder(self.nsims))
        self.assertEqual(local_manager.exp_data['exp_name'], 'test')

    def test_status(self):
        local_manager = ExperimentManagerFactory.from_file(utils.exp_file())
        states, msgs = local_manager.get_simulation_status()
        self.assertListEqual(states.values(), ['Running'] * self.nsims)

        if os.name != 'posix':  # TODO: resolve permissions issues with process.kill functionality on Mac
            local_manager.cancel_simulations(killall=True)
            states, msgs = local_manager.get_simulation_status()
            self.assertListEqual(states.values(), ['Failed'] * self.nsims)

            self.assertRaises(NotImplementedError, lambda: local_manager.resubmit_simulations(resubmit_all_failed=True))


if __name__ == '__main__':
    unittest.main()
