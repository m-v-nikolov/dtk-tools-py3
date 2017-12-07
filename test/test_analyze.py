import unittest
import simtools.AnalyzeManager.AnalyzeHelper as AnalyzeHelper


class TestAnalyze(unittest.TestCase):
    """
    Environment:
    server_endpoint = https://comps2.idmod.org
    environment = Bayesian

    suite_id
    d0993489-7cdb-e711-80c6-f0921c167864

        exp_id
        d1993489-7cdb-e711-80c6-f0921c167864
            sim_id
            dd993489-7cdb-e711-80c6-f0921c167864
            dc993489-7cdb-e711-80c6-f0921c167864


        exp_id
        31a66f9d-7cdb-e711-80c6-f0921c167864
            sim_id
            3da66f9d-7cdb-e711-80c6-f0921c167864
            3ca66f9d-7cdb-e711-80c6-f0921c167864

    ----------------------------------------------------
    suite_id
    9867a9c1-6fdb-e711-80c6-f0921c167864

        exp_id
        9967a9c1-6fdb-e711-80c6-f0921c167864
            sim_id
            a567a9c1-6fdb-e711-80c6-f0921c167864
            a467a9c1-6fdb-e711-80c6-f0921c167864

        exp_id
        08a51adc-6fdb-e711-80c6-f0921c167864
            sim_id
            14a51adc-6fdb-e711-80c6-f0921c167864
            13a51adc-6fdb-e711-80c6-f0921c167864
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @unittest.skip("demonstrating skipping")
    def test_one_suite(self):
        """
        suite_id = 'd0993489-7cdb-e711-80c6-f0921c167864'
        """
        print('1 Suite.')

        itemids = ['d0993489-7cdb-e711-80c6-f0921c167864']

        # collect all experiments and simulations
        exp_dict, sim_dict = AnalyzeHelper.collect_experiments_simulations(itemids)

        self.output(exp_dict, sim_dict)

        self.assertTrue(isinstance(exp_dict, dict))
        self.assertTrue(isinstance(sim_dict, dict))
        self.assertEqual(2, len(exp_dict))
        self.assertEqual(0, len(sim_dict))

    @unittest.skip("demonstrating skipping")
    def test_one_experiment(self):
        """
        exp_id = 'd1993489-7cdb-e711-80c6-f0921c167864'
        """
        print('1 Experiment.')

        itemids = ['d1993489-7cdb-e711-80c6-f0921c167864']

        # collect all experiments and simulations
        exp_dict, sim_dict = AnalyzeHelper.collect_experiments_simulations(itemids)

        self.output(exp_dict, sim_dict)

        self.assertTrue(isinstance(exp_dict, dict))
        self.assertTrue(isinstance(sim_dict, dict))
        self.assertEqual(1, len(exp_dict))
        self.assertEqual(0, len(sim_dict))

    @unittest.skip("demonstrating skipping")
    def test_one_simulation(self):
        """
        sim_id = 'dd993489-7cdb-e711-80c6-f0921c167864'
        """
        print('1 Simulation.')

        itemids = ['dd993489-7cdb-e711-80c6-f0921c167864']

        # collect all experiments and simulations
        exp_dict, sim_dict = AnalyzeHelper.collect_experiments_simulations(itemids)

        self.output(exp_dict, sim_dict)

        self.assertTrue(isinstance(exp_dict, dict))
        self.assertTrue(isinstance(sim_dict, dict))
        self.assertEqual(0, len(exp_dict))
        self.assertEqual(1, len(sim_dict))

    @unittest.skip("demonstrating skipping")
    def test_one_experiment_one_simulation(self):
        # positive test
        """
        exp_id = 'd1993489-7cdb-e711-80c6-f0921c167864'
        sim_id = 'dd993489-7cdb-e711-80c6-f0921c167864'
        """
        print('1 Experiment and 1 Simulation.')

        itemids = ['d1993489-7cdb-e711-80c6-f0921c167864', 'dd993489-7cdb-e711-80c6-f0921c167864']

        # collect all experiments and simulations
        exp_dict, sim_dict = AnalyzeHelper.collect_experiments_simulations(itemids)

        self.output(exp_dict, sim_dict)

        self.assertTrue(isinstance(exp_dict, dict))
        self.assertTrue(isinstance(sim_dict, dict))
        self.assertEqual(1, len(exp_dict))
        self.assertEqual(1, len(sim_dict))

    @unittest.skip("demonstrating skipping")
    def test_one_experiment_one_simulation_one_suite(self):
        """
        suite_id = 'd0993489-7cdb-e711-80c6-f0921c167864'
        exp_id = 'd1993489-7cdb-e711-80c6-f0921c167864'     # exp belong to suite
        sim_id = 'dd993489-7cdb-e711-80c6-f0921c167864'
        """
        print('1 Experiment, 1 Simulation and 1 Suite (exp belong to suite.)')

        itemids = ['d0993489-7cdb-e711-80c6-f0921c167864', 'd1993489-7cdb-e711-80c6-f0921c167864', 'dd993489-7cdb-e711-80c6-f0921c167864' ]

        # collect all experiments and simulations
        exp_dict, sim_dict = AnalyzeHelper.collect_experiments_simulations(itemids)

        self.output(exp_dict, sim_dict)

        self.assertTrue(isinstance(exp_dict, dict))
        self.assertTrue(isinstance(sim_dict, dict))
        self.assertEqual(2, len(exp_dict))
        self.assertEqual(1, len(sim_dict))

    @unittest.skip("demonstrating skipping")
    def test_one_experiment_one_simulation_one_suite_2(self):
        """
        suite_id = 'd0993489-7cdb-e711-80c6-f0921c167864'
        exp_id = '9967a9c1-6fdb-e711-80c6-f0921c167864'     # exp not belong to suite
        sim_id = 'dd993489-7cdb-e711-80c6-f0921c167864'
        """
        print('1 Experiment, 1 Simulation and 1 Suite (exp not belong to suite.)')
        itemids = ['d0993489-7cdb-e711-80c6-f0921c167864', '9967a9c1-6fdb-e711-80c6-f0921c167864', 'dd993489-7cdb-e711-80c6-f0921c167864' ]

        # collect all experiments and simulations
        exp_dict, sim_dict = AnalyzeHelper.collect_experiments_simulations(itemids)

        self.output(exp_dict, sim_dict)

        self.assertTrue(isinstance(exp_dict, dict))
        self.assertTrue(isinstance(sim_dict, dict))
        self.assertEqual(3, len(exp_dict))
        self.assertEqual(1, len(sim_dict))

    # Help functions
    @classmethod
    def output(cls, exp_dict, sim_dict):
        exp_len = len(exp_dict)
        sim_len = len(sim_dict)
        print('Consolidated Experiments (count=%s):' % exp_len)
        if exp_len > 0:
            el = [' - %s' % exp_id for exp_id in exp_dict.keys()]
            print('\n'.join(el))

        print('Simulations (count=%s):' % sim_len)
        if sim_len > 0:
            sl = [' - %s' % sim_id for sim_id in sim_dict.keys()]
            print('\n'.join(sl))

# class TestAnalyze

if __name__ == '__main__':
    unittest.main()