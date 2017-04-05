import logging
import os

import copy
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import pandas as pd
import seaborn as sns
from simtools.OutputParser import CompsDTKOutputParser

from calibtool.utils import ResumePoint

from calibtool.plotters.BasePlotter import BasePlotter

sns.set_style('white', {'axes.linewidth': 0.5})

logger = logging.getLogger(__name__)


class SiteDataPlotter(BasePlotter):
    def __init__(self, combine_sites=True, num_to_plot=5):
        super(SiteDataPlotter, self).__init__(combine_sites)
        self.num_to_plot = num_to_plot

    @property
    def directory(self):
        return self.get_plot_directory()

    def get_site_analyzer(self, site_name, analyzer_name):
        for site in self.manager.sites:
            if site_name != site.name:
                continue
            for analyzer in site.analyzers:
                if analyzer_name == analyzer.name:
                    return analyzer
        raise Exception('Unable to find analyzer=%s for site=%s' % (analyzer_name, site_name))

    def get_analyzer_data(self, iteration, site_name, analyzer_name):
        site_analyzer = '%s_%s' % (site_name, analyzer_name)
        return self.manager.state_for_iteration(iteration).analyzers[site_analyzer]

    def visualize(self):
        iteration_status = self.manager.status
        if iteration_status != ResumePoint.next_point:
            return  # Only plot once results are available

        if self.combine_sites:
            for site_name, analyzer_names in self.site_analyzer_names.items():
                sorted_results = self.all_results.sort_values(by='total', ascending=False).reset_index()
                self.plot_analyzers(site_name, analyzer_names, sorted_results)
        else:
            for site_name, analyzer_names in self.site_analyzer_names.items():
                self.combine_by_site(site_name, analyzer_names, self.all_results)
                sorted_results = self.all_results.sort_values(by='%s_total' % site_name, ascending=False).reset_index()
                self.plot_analyzers(site_name, analyzer_names, sorted_results)

         # Data needed for the LL_CSV
        self.location = self.manager.location
        self.iteration_state = self.manager.iteration_state
        self.iteration = self.manager.iteration
        self.suite_id = self.manager.suite_id
        try:
            self.write_LL_csv(self.manager.exp_manager.experiment)
        except:
            logger.info("Log likelihood CSV could not be created. Skipping...")

    def plot_analyzers(self, site_name, analyzer_names, samples):
        cmin, cmax = samples['total'].describe()[['min', 'max']].tolist()
        cmin = cmin if cmin < cmax else cmax - 1  # avoid divide by zero in color range

        for analyzer_name in analyzer_names:
            site_analyzer = '%s_%s' % (site_name, analyzer_name)
            try:
                os.makedirs(os.path.join(self.directory, site_analyzer))
            except:
                pass

            self.plot_best(site_name, analyzer_name, samples.iloc[:self.num_to_plot])
            self.plot_all(site_name, analyzer_name, samples, clim=(cmin, cmax))

    def plot_best(self, site_name, analyzer_name, samples):

        analyzer = self.get_site_analyzer(site_name, analyzer_name)

        for iteration, iter_samples in samples.groupby('iteration'):
            analyzer_data = self.get_analyzer_data(iteration, site_name, analyzer_name)

            for rank, sample in iter_samples['sample'].iteritems():  # index is rank
                fname = os.path.join(self.directory, '%s_%s' % (site_name, analyzer_name), 'rank%d' % rank)
                fig = plt.figure(fname, figsize=(4, 3))

                analyzer.plot_comparison(fig, analyzer_data['samples'][sample], fmt='-o', color='#CB5FA4', alpha=1, linewidth=1)
                analyzer.plot_comparison(fig, analyzer_data['ref'], fmt='-o', color='#8DC63F', alpha=1, linewidth=1, reference=True)

                fig.set_tight_layout(True)

                plt.savefig(fname + '.pdf', format='PDF')
                plt.close(fig)

    def plot_all(self, site_name, analyzer_name, samples, clim):

        analyzer = self.get_site_analyzer(site_name, analyzer_name)

        fname = os.path.join(self.directory, '%s_%s_all' % (site_name, analyzer_name))
        fig = plt.figure(fname, figsize=(4, 3))
        cmin, cmax = clim

        for iteration, iter_samples in samples.groupby('iteration'):
            analyzer_data = self.get_analyzer_data(iteration, site_name, analyzer_name)
            results_by_sample = iter_samples.reset_index().set_index('sample')['total']
            for sample, result in results_by_sample.iteritems():
                analyzer.plot_comparison(fig, analyzer_data['samples'][sample], fmt='-',
                              color=cm.Blues((result - cmin) / (cmax - cmin)), alpha=0.5, linewidth=0.5)

        analyzer.plot_comparison(fig, analyzer_data['ref'], fmt='-o', color='#8DC63F', alpha=1, linewidth=1, reference=True)

        fig.set_tight_layout(True)
        plt.savefig(fname + '.pdf', format='PDF')
        plt.close(fig)

    def cleanup(self):
        """
        cleanup the existing plots
        :param calib_manager:
        :return:
        """
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
        best_samples = samples.iloc[:self.num_to_plot]
        for analyzer in analyzers:
            site_analyzer = '%s_%s' % (site, analyzer)
            self.cleanup_plot_for_best(site_analyzer, best_samples)
            self.cleanup_plot_for_all(site_analyzer)

    def cleanup_plot_for_best(self, site_analyzer, samples):
        """
        cleanup the existing plots
        :param site_analyzer:
        :param samples:
        :return:
        """
        for iteration, iter_samples in samples.groupby('iteration'):
            for rank, sample in iter_samples['sample'].iteritems():  # index is rank
                fname = os.path.join(self.directory, site_analyzer, 'rank%d' % rank)
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
        fname = os.path.join(self.directory, '%s_all' % site_analyzer)
        plot_path = fname + '.pdf'
        if os.path.exists(plot_path):
            try:
                # logger.info("Try to delete %s" % plot_path)
                os.remove(plot_path)
            except OSError:
                logger.error("Failed to delete %s" % plot_path)

    def write_LL_csv(self, experiment):
        """
        Write the LL_summary.csv with what is in the CalibManager
        """
        # Deep copy all_results ato not disturb the calibration
        all_results = self.all_results.copy(True)

        # Index the likelihood-results DataFrame on (iteration, sample) to join with simulation info
        results_df = all_results.reset_index().set_index(['iteration', 'sample'])

        # Get the simulation info from the iteration state
        siminfo_df = pd.DataFrame.from_dict(self.iteration_state.simulations, orient='index')
        siminfo_df.index.name = 'simid'
        siminfo_df['iteration'] = self.iteration
        siminfo_df = siminfo_df.rename(columns={'__sample_index__': 'sample'}).reset_index()

        # Group simIDs by sample point and merge back into results
        grouped_simids_df = siminfo_df.groupby(['iteration', 'sample']).simid.agg(lambda x: tuple(x))
        results_df = results_df.join(grouped_simids_df, how='right')  # right: only this iteration with new sim info

        # TODO: merge in parameter values also from siminfo_df (sample points and simulation tags need not be the same)

        # Retrieve the mapping between simID and output file path
        if self.location == "HPC":
            sims_paths = CompsDTKOutputParser.createSimDirectoryMap(suite_id=self.suite_id, save=False)
        else:
            sims_paths = {sim.id: os.path.join(experiment.get_path(), sim.id) for sim in experiment.simulations}

        # Transform the ids in actual paths
        def find_path(el):
            paths = list()
            try:
                for e in el:
                    paths.append(sims_paths[e])
            except Exception as ex:
                pass # [TODO]: fix issue later.
            return ",".join(paths)

        results_df['outputs'] = results_df['simid'].apply(find_path)
        del results_df['simid']

        # Concatenate with any existing data from previous iterations and dump to file
        csv_path = os.path.join(self.directory, 'LL_all.csv')
        if os.path.exists(csv_path):
            current = pd.read_csv(csv_path, index_col=['iteration', 'sample'])
            results_df = pd.concat([current, results_df])
        results_df.sort_values(by='total', ascending=True).to_csv(csv_path)