import os
import stat
import unittest

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from simtools.DataAccess.DataStore import DataStore
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.ModBuilder import ModBuilder, SingleSimulationBuilder, RunNumberSweepBuilder, ModFn
from simtools.SetupParser import SetupParser
from simtools.SimConfigBuilder import SimConfigBuilder
from simtools.Utilities.General import get_md5, CommandlineGenerator
from COMPS.Data.Simulation import SimulationState


class TestConfigBuilder(unittest.TestCase):

    def setUp(self):
        self.cb = SimConfigBuilder.from_defaults('DUMMY')
        SetupParser.init(selected_block='LOCAL')
        self.input_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'input')
        self.dummy_exe_folder = os.path.join(self.input_path, 'dummy_exe_folder')
        self.another_dummy_exe_folder = os.path.join(self.input_path, 'another_dummy_exe_folder')

    def tearDown(self):
        SetupParser._uninit()

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
        self.assertListEqual(s.keys(), ['config.json'])
        self.assertDictEqual(eval(s['config.json']), dict(Simulation_Type='DUMMY'))

    def test_dump_to_file(self):
        self.cb.dump_files(os.getcwd())
        self.assertTrue(os.path.exists('config.json'))
        os.remove('config.json')

    def test_stage_exe(self):
        local_setup = dict(SetupParser.items())

        file1 = os.path.join(self.dummy_exe_folder,'dummy_exe.txt')
        md5 = get_md5(file1)
        self.cb.stage_executable(file1, SetupParser.get('bin_staging_root'))
        staged_dir = os.path.join(SetupParser.get('bin_staging_root'), md5)
        staged_path = os.path.join(staged_dir, 'dummy_exe.txt')
        self.assertTrue(os.path.exists(staged_path))

        file2 = os.path.join(self.another_dummy_exe_folder,'dummy_exe.txt')
        os.chmod(file2, stat.S_IREAD)  # This is not writeable, but should not error because it isn't copied
        another_md5 = get_md5(file2)
        self.cb.stage_executable(file2, SetupParser.get('bin_staging_root'))
        self.assertEqual(md5, another_md5)

        self.cb.stage_executable('\\\\remote\\path\\to\\file.exe', local_setup)

        os.remove(staged_path)
        os.rmdir(staged_dir)

    def test_commandline(self):
        commandline = self.cb.get_commandline('input/file.txt', dict(SetupParser.items()))
        self.assertEqual('input/file.txt', commandline.Commandline)

        another_command = CommandlineGenerator('input/file.txt', {'--config': 'config.json'}, [])
        self.assertEqual('input/file.txt --config config.json', another_command.Commandline)


class TestConfigExceptions(unittest.TestCase):

    def test_bad_kwargs(self):
        self.assertRaises(Exception, lambda: SimConfigBuilder.from_defaults('DUMMY', Not_A_Climate_Parameter=26))

    def test_no_simtype(self):
        self.assertRaises(Exception, lambda: SimConfigBuilder.from_defaults())


class TestBuilders(unittest.TestCase):

    def setUp(self):
        ModBuilder.metadata = {}
        self.cb = SimConfigBuilder.from_defaults('DUMMY')

    def test_param_fn(self):
        k, v = ('foo', 'bar')
        fn = ModFn(SimConfigBuilder.set_param, k, v)
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

        fn = ModFn(custom_fn, 'foo', 'bar', value=v)
        fn(self.cb)
        self.assertListEqual(self.cb.get_param('nested')['foo']['bar'], v)
        self.assertEqual(ModBuilder.metadata, {'foo.bar': v})


class TestLocalExperimentManager(unittest.TestCase):

    nsims = 3

    def setUp(self):
        SetupParser.init(selected_block='LOCAL')

    def tearDown(self):
        SetupParser._uninit()

    def test_run(self):
        input_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'input')
        model_file = os.path.join(input_path, 'dummy_model.py')
        config_builder = DTKConfigBuilder.from_defaults('VECTOR_SIM')
        local_manager = ExperimentManagerFactory.from_model(model_file, 'LOCAL', config_builder=config_builder)
        local_manager.run_simulations(exp_builder=RunNumberSweepBuilder(self.nsims))
        self.assertEqual(local_manager.experiment.exp_name, 'test')
        experiment = local_manager.experiment

        local_manager = ExperimentManagerFactory.from_experiment(experiment=DataStore.get_experiment(experiment.exp_id))
        states, msgs = local_manager.get_simulation_status()
        self.assertListEqual(states.values(), [SimulationState.Created] * self.nsims)

        local_manager.hard_delete()
        import time
        time.sleep(3)


if __name__ == '__main__':
    unittest.main()
