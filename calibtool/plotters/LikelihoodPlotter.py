import logging
import os

import matplotlib.pyplot as plt

from calibtool.plotters.BasePlotter import BasePlotter
from calibtool.visualize import combine_by_site

logger = logging.getLogger(__name__)

try:
    import seaborn as sns
    sns.set_style('white')
except:
    pass

class LikelihoodPlotter(BasePlotter):
    def __init__(self, combine_sites=True):
        super(LikelihoodPlotter, self).__init__( combine_sites)

    def visualize(self, calib_manager):
        self.all_results = calib_manager.all_results
        logger.debug(self.all_results)

        self.directory = calib_manager.iteration_directory()
        self.param_names = calib_manager.param_names()
        self.site_analyzer_names = calib_manager.site_analyzer_names()

        if self.combine_sites:
            self.plot_by_parameter()
        else:
            self.plot_by_parameter_and_site()

    def plot_by_parameter_and_site(self):

        for site, analyzers in self.site_analyzer_names.items():
            combine_by_site(site, analyzers, self.all_results)
            self.plot_by_parameter(site=site)

    def plot_by_parameter(self, site='', **kwargs):

        for param in self.param_names:

            fig = plt.figure('LL by parameter ' + param, figsize=(5, 4))
            ax = fig.add_subplot(111)
            plt.subplots_adjust(left=0.15, bottom=0.15)

            total = site + '_total' if site else 'total'
            results = self.all_results[[total, 'iteration', param]]
            self.plot1d_by_iteration(results, param, total, **kwargs)

            ax.set(
                # TODO: get source for sample range and type info
                # xlim=(), xscale='log' if is_log(param) else 'linear',
                xlabel=param, ylabel='log likelihood')

            try:
                os.makedirs(os.path.join(self.directory, site))
            except:
                pass

            plt.savefig(os.path.join(self.directory, site, 'LL_%s.pdf' % param),
                        format='PDF')
            plt.close(fig)

    def plot1d_by_iteration(self, results, param, total, **kwargs):

        iterations = results.groupby('iteration', sort=True)
        n_iterations = len(iterations)

        colors = ['#4BB5C1'] * (n_iterations - 1) + ['#FF2D00']

        for iter, values in iterations:
            sorted_values = values.sort_values(by=param)
            plt.plot(sorted_values[param], sorted_values[total],
                     color=colors[iter],
                     linewidth=(iter + 1) / (n_iterations + 1.) * 2,
                     alpha=(iter + 1) / (n_iterations + 1.),
                     **kwargs)
