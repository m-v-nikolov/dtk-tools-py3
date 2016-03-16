import copy
import json
import os
import shutil
import unittest

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import norm, uniform, multivariate_normal

from calibtool.IterationState import IterationState
from calibtool.Prior import MultiVariatePrior
from calibtool.algo.IMIS import IMIS


class TestCommands(unittest.TestCase):
    def setUp(self):
        self.current_cwd = os.getcwd()
        os.mkdir('calibration')
        shutil.copy('../examples/example_calibration.py', 'calibration')

    def tearDown(self):
        # Change the dir back to normal
        os.chdir(self.current_cwd)
        shutil.rmtree('calibration')

    def test_run_calibration(self):
        os.chdir('calibration')
        os.system('calibtool run example_calibration.py')
        # Test if files are present
        self.assertTrue(os.path.exists('ExampleCalibration'))
        self.assertTrue(os.path.exists('ExampleCalibration/_plots'))
        self.assertNotEqual(len(os.listdir('ExampleCalibration/_plots')), 0)
        self.assertTrue(os.path.exists('ExampleCalibration/iter0'))
        self.assertTrue(os.path.exists('ExampleCalibration/iter1'))
        self.assertTrue(os.path.exists('ExampleCalibration/CalibManager.json'))
        #self.assertTrue(os.path.exists('ExampleCalibration/LL_summary.csv'))


    def test_reanalyze(self):
        # Run the calibration
        os.chdir('calibration')
        os.system('calibtool run example_calibration.py')

        # Open the CalibManager.json and save the values
        with open('ExampleCalibration/CalibManager.json', 'r') as fp:
            cm = json.load(fp)
            self.totals = cm['results']['total']

        # Now reanalyze
        os.system('calibtool reanalyze example_calibration.py')
        # After reanalyze compare the totals
        with open('ExampleCalibration/CalibManager.json', 'r') as fp:
            cm = json.load(fp)
            for i in range(len(self.totals)):
                self.assertAlmostEqual(cm['results']['total'][i], self.totals[i])



class TestMultiVariatePrior(unittest.TestCase):

    def test_two_normals(self):
        two_normals = MultiVariatePrior(name='two_normals', functions=(norm(loc=0, scale=1), norm(loc=-10, scale=1)))

        xx = two_normals.rvs(size=1000)
        np.testing.assert_almost_equal(xx.mean(axis=0), np.array([0, -10]), decimal=1)
        np.testing.assert_almost_equal(xx.std(axis=0), np.array([1, 1]), decimal=1)

        xx = two_normals.rvs(size=1)
        self.assertEqual(xx.shape, (2,))

    def test_normal_by_uniform(self):
        normal_by_uniform = MultiVariatePrior(name='normal_by_uniform', functions=(norm(loc=0, scale=1), uniform(loc=-10, scale=5)))

        xx = normal_by_uniform.rvs(size=1000)
        np.testing.assert_almost_equal(xx.mean(axis=0), np.array([0, -7.5]), decimal=1)
        np.testing.assert_almost_equal(xx.std(axis=0), np.array([1, 5/np.sqrt(12)]), decimal=1)

    def test_uniform_pdf(self):
        uniform_prior = MultiVariatePrior.by_param(a=uniform(loc=0, scale=2))
        test = np.array([-1, 0, 1, 1.5, 2, 2.5])
        output = uniform_prior.pdf(test).tolist()
        self.assertListEqual(output, [0, 0.5, 0.5, 0.5, 0.5, 0])

    def test_two_uniform_pdf(self):
        uniform_prior = MultiVariatePrior.by_param(a=uniform(loc=0, scale=2),
                                                   b=uniform(loc=0, scale=2))
        test = np.array([[-1, 0], [0, 1], [1.5, 2], [-1, 2.5]])
        output = uniform_prior.pdf(test).tolist()
        self.assertListEqual(output, [0, 0.25, 0.25, 0])


class NextPointTestWrapper(object):
    '''
    A simple wrapper for running iterative loops without all the CalibManager overhead.
    '''

    def __init__(self, algo, likelihood_fn):
        self.algo = algo
        self.likelihood_fn = likelihood_fn

    def run(self, max_iterations=100):
        for iteration in range(max_iterations):
            next_samples = self.algo.get_next_samples()
            next_likelihoods = self.likelihood_fn(next_samples)
            self.algo.update_results(next_likelihoods)
            self.algo.update_state(iteration)
            if self.algo.end_condition():
                break
        return self.algo.get_final_samples()

    def save_figure(self, fig, name):
        try:
            os.makedirs('tmp')
        except:
            pass  # directory already exists
        fig.savefig(os.path.join('tmp', '%s.png' % name))


class TestIMIS(unittest.TestCase):

    def test_multivariate(self):
        likelihood_fn = lambda x: multivariate_normal(mean=[1, 1], cov=[[1, 0.6], [0.6, 1]]).pdf(x)
        prior_fn = multivariate_normal(mean=[0, 0], cov=3*np.identity(2))

        x, y = np.mgrid[-5:5:0.01, -5:5:0.01]
        pos = np.empty(x.shape + (2,))
        pos[:, :, 0] = x
        pos[:, :, 1] = y
        true_posterior = likelihood_fn(pos) * prior_fn.pdf(pos)

        imis = IMIS(prior_fn, initial_samples=5000, samples_per_iteration=500)
        tester = NextPointTestWrapper(imis, likelihood_fn)
        resample = tester.run()

        fig_name = 'test_multivariate'
        fig, (ax1, ax2) = plt.subplots(1, 2, num=fig_name, figsize=(11, 5))
        ax1.hist(imis.weights, bins=50, alpha=0.3)
        ax1.hist(resample['weights'], bins=50, alpha=0.3, color='firebrick')
        ax1.set_title('Weights')
        ax2.hexbin(*zip(*resample['samples']), gridsize=50, cmap='Blues', mincnt=0.01)
        ax2.contour(x, y, true_posterior, cmap='Reds')
        ax2.set(xlim=[-2, 3], ylim=[-2, 3], title='Resamples')
        fig.set_tight_layout(True)
        tester.save_figure(fig, fig_name)

    def test_univariate(self):
        likelihood_fn = lambda xx: 2 * np.exp(-np.sin(3*xx) * np.sin(xx**2) - 0.1*xx**2)
        prior_fn = multivariate_normal(mean=[0], cov=[5**2])

        xx = np.arange(-5, 5, 0.01)
        true_posterior = np.multiply(likelihood_fn(xx), prior_fn.pdf(xx))

        imis = IMIS(prior_fn, initial_samples=5000, samples_per_iteration=500)
        tester = NextPointTestWrapper(imis, likelihood_fn)
        resample = tester.run()

        fig_name = 'test_univariate'
        fig = plt.figure(fig_name, figsize=(10, 5))
        plt.plot(xx, prior_fn.pdf(xx), 'navy', label='Prior')
        plt.plot(xx, true_posterior, 'r', label='Posterior')
        plt.hist(resample['samples'], bins=100, alpha=0.3, label='Resamples', normed=True)
        plt.xlim([-5, 5])
        plt.legend()
        fig.set_tight_layout(True)
        tester.save_figure(fig, fig_name)


class TestIterationState(unittest.TestCase):

    init_state = dict(parameters={}, next_point={}, simulations={},
                      analyzers={}, results=[], iteration=0)

    def setUp(self):
        self.state = IterationState()

    def example_settings(self):
        self.state.parameters = dict(values=[[0, 1], [2, 3], [4, 5]], names=['p1', 'p2'])
        prior = MultiVariatePrior.by_param(a=uniform(loc=0, scale=2))
        self.state.next_point = IMIS(prior).get_current_state()
        self.state.simulations = {
            'sims': {'id1': {'p1': 1, 'p2': 2},
                     'id2': {'p1': 3, 'p2': 4}}}
        self.state.analyzers = {'a1': [{'x': [1, 2], 'y': [3, 4]},
                                       {'x': [1, 2], 'y': [5, 6]}]}
        self.state.results = [{'a1': -13, 'total': -13},
                              {'a1': -11, 'total': -11}]

    def test_init(self):
        self.assertDictEqual(self.state.__dict__,
                             self.init_state)

    def test_increment_iteration(self):
        self.example_settings()
        self.state.increment_iteration()
        self.assertEqual(self.state.iteration, 1)
        iter1_init_state = copy.deepcopy(self.init_state)
        iter1_init_state.update(dict(iteration=1))
        self.assertDictEqual(self.state.__dict__,
                             iter1_init_state)

    def test_serialization(self):
        self.example_settings()
        self.state.to_file('tmp.json')
        new_state = IterationState.from_file('tmp.json')
        old_state = copy.deepcopy(self.state)
        next_point_new = new_state.__dict__.pop('next_point')
        next_point_old = old_state.__dict__.pop('next_point')
        self.assertDictEqual(new_state.__dict__, old_state.__dict__)
        np.testing.assert_array_equal(next_point_new['latest_samples'],
                                      next_point_old['latest_samples'])
        os.remove('tmp.json')

    def test_reset_to_step(self):
        self.example_settings()
        self.assertEqual(self.state.results[0]['a1'], -13)
        self.state.reset_to_step(iter_step='analyze')
        self.assertEqual(self.state.results, [])
        self.assertEqual(self.state.analyzers, {})
        self.assertEqual(self.state.simulations['sims']['id1']['p1'], 1)
        self.state.reset_to_step(iter_step='commission')
        self.assertEqual(self.state.simulations, {})
        self.assertEqual(self.state.parameters['values'][2][1], 5)


class TestNumpyDecoder(unittest.TestCase):

    '''
    This was discovered in caching CalibAnalyzer array with np.int64
    age_bins, which is not well handled by the utils.NumpyEncoder class.
    ''' 

    def tearDown(self):
        os.remove('int32.json')

    def test_int32_conversion(self, asint32=True):
        df = pd.DataFrame({'x': [1, 2], 'y': [2.8, 4.2]})
        if asint32:
            df.x = df.x.astype(int)  # now np.int64 is np.int32
        a = {'ana': [df.to_dict(orient='list')]}
        state = IterationState(analyzers=a)
        state.to_file('int32.json')

    def test_int64_exception(self):
        with self.assertRaises(RuntimeError) as err:
            self.test_int32_conversion(False)


class TestCalibManager(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
