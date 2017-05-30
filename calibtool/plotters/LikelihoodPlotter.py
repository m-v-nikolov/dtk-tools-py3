import logging
import os
import matplotlib.pyplot as plt
import seaborn as sns
from calibtool.utils import StatusPoint
from calibtool.plotters.BasePlotter import BasePlotter

sns.set_style('white')

logger = logging.getLogger(__name__)


class LikelihoodPlotter(BasePlotter):
    def __init__(self, combine_sites=True):
        super(LikelihoodPlotter, self).__init__(combine_sites)

    @property
    def param_names(self):
        return self.iteration_state.param_names

    @property
    def prior_fn(self):
        return self.iteration_state.next_point.prior_fn

    @property
    def directory(self):
        return self.get_iteration_directory()

    def visualize(self, iteration_state):
        self.iteration_state = iteration_state
        self.site_analyzer_names = iteration_state.site_analyzer_names
        iteration_status = self.iteration_state.status
        if iteration_status != StatusPoint.plot:
            return  # Only plot once results are available

        if self.combine_sites:
            self.plot_by_parameter()
        else:
            self.plot_by_parameter_and_site()

    def plot_by_parameter_and_site(self):
        for site, analyzers in self.site_analyzer_names.items():
            self.combine_by_site(site, analyzers, self.all_results)
            self.plot_by_parameter(site=site)

    def plot_by_parameter(self, site='', **kwargs):

        for param in self.param_names:
            fig = plt.figure('LL by parameter ' + param, figsize=(5, 4))
            ax = fig.add_subplot(111)

            total = site + '_total' if site else 'total'
            results = self.all_results[[total, 'iteration', param]]
            self.plot1d_by_iteration(results, param, total, **kwargs)

            try:
                sample_range = self.prior_fn.sample_functions[param].sample_range
                if sample_range.is_log():
                    ax.set_xscale('log')
                ax.set_xlim(sample_range.get_xlim())
            except (KeyError, AttributeError):
                pass

            ax.set(xlabel=param, ylabel='log likelihood')

            try:
                os.makedirs(os.path.join(self.directory, site))
            except:
                pass

            fig.set_tight_layout(True)
            plt.savefig(os.path.join(self.directory, site, 'LL_%s.pdf' % param), format='PDF')
            plt.close(fig)

    @staticmethod
    def plot1d_by_iteration(results, param, total, **kwargs):
        iterations = results.groupby('iteration', sort=True)
        n_iterations = len(iterations)

        colors = ['#4BB5C1'] * (n_iterations - 1) + ['#FF2D00']

        for iteration, values in iterations:
            sorted_values = values.sort_values(by=param)
            plt.plot(sorted_values[param], sorted_values[total],
                     color=colors[iteration],
                     linewidth=(iteration + 1) / (n_iterations + 1.) * 2,
                     alpha=(iteration + 1) / (n_iterations + 1.),
                     **kwargs)

    def cleanup(self):
        """
        cleanup the existing plots
        :return:
        """
        if self.combine_sites:
            self.cleanup_plot_by_parameter()
        else:
            self.cleanup_plot_by_parameter_and_site()

    def cleanup_plot_by_parameter_and_site(self):
        """
        cleanup the existing plots
        :return:
        """
        for site, analyzers in self.site_analyzer_names.items():
            self.cleanup_plot_by_parameter(site=site)

    def cleanup_plot_by_parameter(self, site=''):
        """
        cleanup the existing plots
        :param site:
        :return:
        """
        for param in self.param_names:
            plot_path = os.path.join(self.directory, site, 'LL_%s.pdf' % param)
            if os.path.exists(plot_path):
                try:
                    # logger.info("Try to delete %s" % plot_path)
                    os.remove(plot_path)
                except OSError:
                    logger.error("Failed to delete %s" % plot_path)
