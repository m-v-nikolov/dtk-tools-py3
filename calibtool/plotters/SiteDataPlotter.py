import logging
import os

import matplotlib.pyplot as plt
import matplotlib.cm as cm
from calibtool.plotters.BasePlotter import BasePlotter
from calibtool.visualize import combine_by_site
from calibtool.analyzers.DTKCalibFactory import DTKCalibFactory
logger = logging.getLogger(__name__)

try:
    import seaborn as sns
    sns.set_style('white')
except:
    pass

class SiteDataPlotter(BasePlotter):
    def __init__(self, combine_sites=True):
        super(SiteDataPlotter, self).__init__( combine_sites)

    def visualize(self, calib_manager):
        self.all_results = calib_manager.all_results.reset_index()
        logger.debug(self.all_results)

        self.num_to_plot = calib_manager.num_to_plot
        self.site_analyzer_names = calib_manager.site_analyzer_names()
        self.state_for_iteration = calib_manager.state_for_iteration
        self.plots_directory = os.path.join(calib_manager.name, '_plots')

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

        analyzer = DTKCalibFactory.get_analyzer(site_analyzer.split('_')[-1])

        for iteration, samples in iter_samples.items():
            analyzer_data = self.state_for_iteration(iteration).analyzers[site_analyzer]
            reference = analyzer_data['reference']
            sims = analyzer_data['sims']
            x, y = analyzer_data['axis_names']
            for sample, rank in zip(samples['sample'], samples['rank']):
                fname = os.path.join(self.plots_directory, site_analyzer, 'rank%d' % rank)
                fig = plt.figure(fname, figsize=(4, 3))
                plt.subplots_adjust(left=0.15, bottom=0.15, right=0.95)
                data = sims[sample]
                try:
                    analyzer.plot_sim(fig, reference, data, x, y, '-o', color='#CB5FA4', alpha=1, linewidth=1)
                    analyzer.plot_reference(fig, reference, data, x, y, '-o', color='#8DC63F', alpha=1, linewidth=1)
                except AttributeError:
                    ax = fig.add_subplot(111)
                    ax.plot(data[x], data[y], '-o', color='#CB5FA4', alpha=1, linewidth=1)
                    ax.plot(reference[x], reference[y], '-o', color='#8DC63F', alpha=1, linewidth=1)
                    ax.set(xlabel=x, ylabel=y)  # TODO: also cache ylim?
                plt.savefig(fname + '.pdf', format='PDF')
                plt.close(fig)

    def plot_all(self, site_analyzer, iter_samples, clim):

        analyzer = DTKCalibFactory.get_analyzer(site_analyzer.split('_')[-1])

        fname = os.path.join(self.plots_directory, '%s_all' % site_analyzer)
        fig = plt.figure(fname, figsize=(4, 3))
        plt.subplots_adjust(left=0.15, bottom=0.15, right=0.95)
        ax = fig.add_subplot(111)
        cmin, cmax = clim

        for iteration, samples in iter_samples.items():
            analyzer_data = self.state_for_iteration(iteration).analyzers[site_analyzer]
            reference = analyzer_data['reference']
            sims = analyzer_data['sims']
            x, y = analyzer_data['axis_names']
            for sample, result in zip(samples['sample'], samples['result']):
                data = sims[sample]
                try:
                    analyzer.plot_sim(fig, reference, data, x, y, '-', color=cm.Blues((result - cmin) / (cmax - cmin)),
                                      alpha=0.5, linewidth=0.5)
                except AttributeError:
                    ax.plot(data[x], data[y], '-', color=cm.Blues((result - cmin) / (cmax - cmin)), alpha=0.5,
                            linewidth=0.5)
                    ax.set(xlabel=x, ylabel=y)  # TODO: also cache ylim?
        try:
            analyzer.plot_reference(fig, reference, data, x, y, '-o', color='#8DC63F', alpha=1, linewidth=1)
        except AttributeError:
            ax.plot(reference[x], reference[y], '-o', color='#8DC63F', alpha=1, linewidth=1)
        plt.savefig(fname + '.pdf', format='PDF')
        plt.close(fig)


    def cleanup_plot(self, calib_manager):
        """
        cleanup the existing plots
        :param calib_manager:
        :return:
        """
        # [TODO]: need this? Looks not!
        self.all_results = calib_manager.all_results.reset_index()

        self.num_to_plot = calib_manager.num_to_plot
        self.site_analyzer_names = calib_manager.site_analyzer_names()
        self.state_for_iteration = calib_manager.state_for_iteration
        self.plots_directory = os.path.join(calib_manager.name, '_plots')

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
