import argparse
import unittest
import dtk.commands_args as CMDarg


class ErrorRaisingArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)

def dummy_function():
    pass

class CommandsArgsTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(CommandsArgsTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.parser = ErrorRaisingArgumentParser(prog='dtk')
        self.flags = []
        self.subparsers = self.parser.add_subparsers(parser_class=ErrorRaisingArgumentParser)
        run_parser = CMDarg.populate_run_arguments(self.subparsers, dummy_function)
        status_parser = CMDarg.populate_status_arguments(self.subparsers, dummy_function)

    def getArgs(self, debug=False):
        if debug:
            print(self.flags)
        args = self.parser.parse_args(self.flags, namespace=None)
        return args

    def tearDown(self):
        pass


    def add_help(self):
        self.flags += ['-h']

    # region run flags
    def run_flag(self):
        self.flags = ['run']

    def run_add_priority(self, target_pri="Normal"):
        self.flags += ['--priority',target_pri]

    def run_add_quiet(self, short_version=False):
        flag = '-q' if short_version else '--quiet'
        self.flags += [flag]

    def run_add_configname(self, config_name="config.json"):
        self.flags += [config_name]

    def run_add_nodegroup(self, node_group="bayesianhpc"):
        self.flags += ['--node_group',node_group]

    def run_add_analyzer(self, analyzer="my_cool_anaylyzer.py", short_version=False):
        key_flag = '-a' if short_version else '--analyzer'
        self.flags += [key_flag, analyzer]

    def run_add_config(self, config_file="config.json"):
        self.flags += [config_file]

    def run_add_blocking(self, short_version=False):
        blocking_flag = '-b' if short_version else '--blocking'
        self.flags += [blocking_flag]

    # endregion

    # region status flags

    def status_flag(self):
        self.flags = ['status']

    def status_add_expid(self, experiment_id):
        self.flags += [str(experiment_id)]

    def status_add_repeat(self, short_version=False):
        status_flag = '-r' if short_version else '--repeat'
        self.flags += [status_flag]

    def status_add_active(self, short_version=False):
        active_flag = '-a' if short_version else '--active'
        self.flags += [active_flag]

    # endregion

    # region run tests
    def test_run_minimal(self):
        figgy = "configgy.json"
        self.run_flag()
        self.run_add_config(figgy)

        args = self.getArgs()

        self.assertEqual(args.config_name, figgy)
        self.assertEqual(args.quiet, False)
        self.assertIsNone(args.priority)
        self.assertIsNone(args.node_group)
        self.assertFalse(args.blocking)
        self.assertFalse(args.quiet)

    def test_run_quiet(self):
        config_file = "cornycornfig.json"
        self.run_flag()
        self.run_add_quiet(short_version=False)
        self.run_add_config(config_file)

        args = self.getArgs()

        self.assertTrue(args.quiet, "--quiet should turn on quiet")
        self.assertEqual(args.config_name, config_file)

    def test_run_q_short(self):
        config_file = "cornycornfig.json"
        self.run_flag()
        self.run_add_quiet(short_version=True)
        self.run_add_config(config_file)

        args = self.getArgs()

        self.assertTrue(args.quiet, "--quiet should turn on quiet")
        self.assertEqual(args.config_name, config_file)

    def test_run_no_config(self):
        self.run_flag()

        with self.assertRaises(ValueError) as cm:
            self.getArgs()

    def test_run_blocking(self):
        config = "config.json"
        self.run_flag()
        self.run_add_config(config)
        self.run_add_blocking(short_version=False)

        args = self.getArgs()

        self.assertEqual(config, args.config_name)
        self.assertTrue(args.blocking, msg="blocking should be True")

    def test_run_b_short(self):
        config = "config.json"
        self.run_flag()
        self.run_add_config(config)
        self.run_add_blocking(short_version=True)

        args = self.getArgs()

        self.assertEqual(config, args.config_name)
        self.assertTrue(args.blocking, msg="blocking should be True")

    def test_run_pri_no_nodegroup(self):
        config = "config.json"
        pri = "BelowNormal"
        self.run_flag()
        self.run_add_config(config)
        self.run_add_priority(pri)

        args = self.getArgs()

        self.assertEqual(config, args.config_name)
        self.assertTrue(args.priority, pri)
        self.assertIsNone(args.node_group)

        pass

    def test_run_nodegroup_no_pri(self):
        config = "config.json"
        nodegroup = "BayesianHPC"
        self.run_flag()
        self.run_add_config(config)
        self.run_add_nodegroup(nodegroup)

        args = self.getArgs()

        self.assertEqual(config, args.config_name)
        self.assertEqual(args.node_group, nodegroup)
        self.assertIsNone(args.priority)

        pass

    def test_run_nodegroup_and_pri(self):
        config = "config.json"
        nodegroup = "BayesianHPC"
        pri = "BelowNormal"
        self.run_flag()
        self.run_add_config(config)
        self.run_add_priority(pri)
        self.run_add_nodegroup(nodegroup)

        args = self.getArgs()

        self.assertEqual(args.config_name, config)
        self.assertEqual(args.node_group, nodegroup)
        self.assertEqual(args.priority, pri)
        pass
    # endregion

    # region help tests
    @unittest.skip("This is not feasbile, see http://goo.gl/a2nfIU")
    def test_run_help(self):
        self.run_flag()
        self.add_help()

        with self.assertRaises(ValueError) as cm:
            self.getArgs(True)

        message = str(cm.exception)
        self.assertIn("usage:", message)
    # endregion

    # region status tests
    def test_status_minimal(self):
        experiment_id = 1234
        self.status_flag()
        self.status_add_expid(experiment_id)

        args = self.getArgs(debug=False)

        self.assertEqual(args.expId, str(experiment_id))
        self.assertFalse(args.repeat)
        self.assertFalse(args.active)

# This test is deprecated until 'dtk status' requires an experiment id again, if ever
#    def test_status_expid_required(self):
#        self.status_flag()
#
#        with self.assertRaises(ValueError) as cm:
#            self.getArgs()
#
#        self.assertIn("too few arguments", cm.exception)

    def test_status_a_r_shorts(self):
        experiment_id = 'Great SIR experiment'
        self.status_flag()
        self.status_add_expid(experiment_id)
        self.status_add_active(True)
        self.status_add_repeat(True)

        args = self.getArgs(debug=False)

        self.assertEqual(args.expId, experiment_id)
        self.assertTrue(args.active)
        self.assertTrue(args.repeat)

    def test_status_repeat_active_longs(self):
        experiment_id = 'Cool households experiment'
        self.status_flag()
        self.status_add_repeat(False)
        self.status_add_active(False)
        self.status_add_expid(experiment_id)

        args = self.getArgs(debug=False)

        self.assertEqual(args.expId, experiment_id)
        self.assertTrue(args.active)
        self.assertTrue(args.repeat)
    # endregion

if __name__ == '__main__':
    unittest.main()
