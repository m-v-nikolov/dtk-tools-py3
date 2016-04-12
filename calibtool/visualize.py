import json
import os
import logging

import matplotlib.pyplot as plt
import matplotlib.cm as cm
import pandas as pd
from calibtool.analyzers.DTKCalibFactory import DTKCalibFactory

try:
    import seaborn as sns
    sns.set_style('white')
except:
    pass

logger = logging.getLogger(__name__)


def combine_by_site(site, analyzers, results):
    site_analyzers = [site + '_' + a for a in analyzers]
    logger.debug('site_analyzers: %s', site_analyzers)
    site_total = site + '_total'
    results[site_total] = results[site_analyzers].sum(axis=1)
    logger.debug('results[%s]=%s', site_total, results[site_total])


class CalibPlotter(object):

    def __init__(self, calib_manager, combine_sites=True):
        pass

    def visualize(self):
        pass


class LikelihoodPlotter(CalibPlotter):

    def __init__(self, calib_manager, combine_sites=True):

        self.all_results = calib_manager.all_results
        logger.debug(self.all_results)

        self.directory = calib_manager.iteration_directory()
        self.param_names = calib_manager.param_names()
        self.site_analyzer_names = calib_manager.site_analyzer_names()

        self.combine_sites = combine_sites

    def visualize(self):

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

            fig = plt.figure('LL by parameter ' + param, figsize=(5,4))
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

        colors = ['#4BB5C1'] * (n_iterations-1) + ['#FF2D00']

        for iter, values in iterations:
            sorted_values = values.sort_values(by=param)
            plt.plot(sorted_values[param], sorted_values[total],
                     color=colors[iter],
                     linewidth=(iter+1) / (n_iterations+1.)*2,
                     alpha=(iter+1) / (n_iterations+1.),
                     **kwargs)


class SiteDataPlotter(CalibPlotter):

    def __init__(self, calib_manager, combine_sites=True):
        self.all_results = calib_manager.all_results.reset_index()
        logger.debug(self.all_results)

        self.num_to_plot = calib_manager.num_to_plot
        self.site_analyzer_names = calib_manager.site_analyzer_names()
        self.state_for_iteration = calib_manager.state_for_iteration
        self.plots_directory = os.path.join(calib_manager.name, '_plots')

        self.combine_sites = combine_sites

    def visualize(self):
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
                fig = plt.figure(fname, figsize=(4,3))
                plt.subplots_adjust(left=0.15, bottom=0.15, right=0.95)
                data = sims[sample]
                try :
                    analyzer.plot_sim(fig, reference, data, x, y, '-o', color='#CB5FA4', alpha=1, linewidth=1)
                    analyzer.plot_reference(fig, reference, data, x, y, '-o', color='#8DC63F', alpha=1, linewidth=1)
                except AttributeError :
                    ax = fig.add_subplot(111)
                    ax.plot(data[x], data[y], '-o', color='#CB5FA4', alpha=1, linewidth=1)
                    ax.plot(reference[x], reference[y], '-o', color='#8DC63F', alpha=1, linewidth=1)                
                    ax.set(xlabel=x, ylabel=y)  # TODO: also cache ylim?
                plt.savefig(fname + '.pdf', format='PDF')
                plt.close(fig)

    def plot_all(self, site_analyzer, iter_samples, clim):

        analyzer = DTKCalibFactory.get_analyzer(site_analyzer.split('_')[-1])

        fname = os.path.join(self.plots_directory, '%s_all' % site_analyzer)
        fig = plt.figure(fname, figsize=(4,3))
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
                try :
                    analyzer.plot_sim(fig, reference, data, x, y, '-', color=cm.Blues((result-cmin)/(cmax-cmin)), alpha=0.5, linewidth=0.5)
                except AttributeError :
                    ax.plot(data[x], data[y], '-', color=cm.Blues((result-cmin)/(cmax-cmin)), alpha=0.5, linewidth=0.5)
                    ax.set(xlabel=x, ylabel=y)  # TODO: also cache ylim?
        try :
            analyzer.plot_reference(fig, reference, data, x, y, '-o', color='#8DC63F', alpha=1, linewidth=1)
        except AttributeError :
            ax.plot(reference[x], reference[y], '-o', color='#8DC63F', alpha=1, linewidth=1)
        plt.savefig(fname + '.pdf', format='PDF')
        plt.close(fig)