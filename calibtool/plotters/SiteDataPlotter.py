import logging
import os

import matplotlib.pyplot as plt
import matplotlib.cm as cm
import pandas as pd
import seaborn as sns

from calibtool.plotters.BasePlotter import BasePlotter
from calibtool.visualize import combine_by_site

sns.set_style('white')

logger = logging.getLogger(__name__)


class SiteDataPlotter(BasePlotter):
    def __init__(self, combine_sites=True, prior_fn={}):
        super(SiteDataPlotter, self).__init__(combine_sites, prior_fn)

    def visualize(self, calib_manager):
        self.all_results = calib_manager.all_results.reset_index()
        logger.debug(self.all_results)

        # TODO: rethink when these are being set, e.g. why not pass calib_manager to __init__?
        self.num_to_plot = calib_manager.num_to_plot
        self.site_analyzer_names = calib_manager.site_analyzer_names()
        self.state_for_iteration = calib_manager.state_for_iteration
        self.plots_directory = os.path.join(calib_manager.name, '_plots')

        # TODO: this is so we can call Analyzer.plot_sim and Analyzer.plot_ref
        # TODO: if these are classmethods, we only need the name, not the instances
        self.analyzers = {}
        for site in calib_manager.sites:
            for analyzer in site.analyzers:
                self.analyzers[site.name+"_"+analyzer.name] = analyzer

        if self.combine_sites:
            for site, analyzers in self.site_analyzer_names.items():
                self.plot_analyzers(site, analyzers, self.all_results)
        else:
            for site, analyzers in self.site_analyzer_names.items():
                combine_by_site(site, analyzers, self.all_results)
                sorted_results = self.all_results.sort_values(by='%s_total' % site, ascending=False)
                self.plot_analyzers(site, analyzers, sorted_results)

    def get_iteration_samples(self, results, subset=False):
        subset = results.iloc[:self.num_to_plot] if subset else results
        samples = {k: {'sample': v['sample'].tolist(),
                       'rank': v.index.tolist(),
                       'result': v['total'].tolist()}
                   for k, v in subset.groupby('iteration')}
        logger.debug(samples)
        return samples

    def plot_analyzers(self, site, analyzers, samples):
        cmin, cmax = samples['total'].describe()[['min', 'max']].tolist()
        cmin = cmin if cmin < cmax else cmax - 1  # avoid divide by zero in color range

        best_samples = self.get_iteration_samples(samples, subset=True)
        all_samples = self.get_iteration_samples(samples)
        for analyzer in analyzers:
            site_analyzer = '%s_%s' % (site, analyzer)
            try:
                os.makedirs(os.path.join(self.plots_directory, site_analyzer))
            except:
                pass
            self.plot_best(site_analyzer, best_samples)
            self.plot_all(site_analyzer, all_samples, clim=(cmin, cmax))

    def plot_best(self, site_analyzer, iter_samples):

        analyzer = self.analyzers[site_analyzer]

        for iteration, samples in iter_samples.items():
            analyzer_data = self.state_for_iteration(iteration).analyzers[site_analyzer]

            for sample, rank in zip(samples['sample'], samples['rank']):
                fname = os.path.join(self.plots_directory, site_analyzer, 'rank%d' % rank)
                fig = plt.figure(fname, figsize=(4, 3))

                analyzer.plot(fig, analyzer_data[str(sample)], '-o', color='#CB5FA4', alpha=1, linewidth=1)
                analyzer.plot(fig, analyzer_data['ref'], '-o', color='#8DC63F', alpha=1, linewidth=1, reference=True)

                plt.savefig(fname + '.pdf', format='PDF')
                plt.close(fig)

    def plot_all(self, site_analyzer, iter_samples, clim):

        analyzer = self.analyzers[site_analyzer]

        fname = os.path.join(self.plots_directory, '%s_all' % site_analyzer)
        fig = plt.figure(fname, figsize=(4, 3))
        cmin, cmax = clim

        for iteration, samples in iter_samples.items():
            analyzer_data = self.state_for_iteration(iteration).analyzers[site_analyzer]
            for sample, result in zip(samples['sample'], samples['result']):
                analyzer.plot(fig, analyzer_data[str(sample)], '-',
                              color=cm.Blues((result - cmin) / (cmax - cmin)), alpha=0.5, linewidth=0.5)

        analyzer.plot(fig, analyzer_data['ref'], '-o', color='#8DC63F', alpha=1, linewidth=1, reference=True)

        plt.savefig(fname + '.pdf', format='PDF')
        plt.close(fig)

    def cleanup_plot(self, calib_manager):
        """
        cleanup the existing plots
        :param calib_manager:
        :return:
        """

        # TODO: if this is done in __init__ we don't need to redo it here?
        self.plots_directory = os.path.join(calib_manager.name, '_plots')  # for directory to remove plots from
        self.num_to_plot = calib_manager.num_to_plot  # for num_to_plot to remove best_samples

        # TODO: use "glob" to find all plots that match site_analyzer_*.pdf pattern?
        if self.combine_sites:
            for site, analyzers in self.site_analyzer_names.items():
                self.cleanup_plot_by_analyzers(site, analyzers, self.all_results)
        else:
            for site, analyzers in self.site_analyzer_names.items():
                self.cleanup_plot_by_analyzers(site, analyzers, self.all_results)

    def cleanup_plot_by_analyzers(self, site, analyzers, samples):
        """
        cleanup the existing plots
        :param site:
        :param analyzers:
        :param samples:
        :return:
        """
        best_samples = self.get_iteration_samples(samples, subset=True)
        for analyzer in analyzers:
            site_analyzer = '%s_%s' % (site, analyzer)
            self.cleanup_plot_for_best(site_analyzer, best_samples)
            self.cleanup_plot_for_all(site_analyzer)

    def cleanup_plot_for_best(self, site_analyzer, iter_samples):
        """
        cleanup the existing plots
        :param site_analyzer:
        :param iter_samples:
        :return:
        """
        for iteration, samples in iter_samples.items():
            for sample, rank in zip(samples['sample'], samples['rank']):
                fname = os.path.join(self.plots_directory, site_analyzer, 'rank%d' % rank)
                plot_path = fname + '.pdf'
                if os.path.exists(plot_path):
                    try:
                        # logger.info("Try to delete %s" % plot_path)
                        os.remove(plot_path)
                        pass
                    except OSError:
                        logger.error("Failed to delete %s" % plot_path)

    def cleanup_plot_for_all(self, site_analyzer):
        """
        cleanup the existing plots
        :param site_analyzer:
        :return:
        """
        fname = os.path.join(self.plots_directory, '%s_all' % site_analyzer)
        plot_path = fname + '.pdf'
        if os.path.exists(plot_path):
            try:
                # logger.info("Try to delete %s" % plot_path)
                os.remove(plot_path)
            except OSError:
                logger.error("Failed to delete %s" % plot_path)
