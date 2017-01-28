import copy
import logging
import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from calibtool.plotters.BasePlotter import BasePlotter
from calibtool.visualize import combine_by_site
from calibtool.utils import ResumePoint
from simtools.OutputParser import CompsDTKOutputParser

sns.set_style('white')

logger = logging.getLogger(__name__)


class LikelihoodPlotter(BasePlotter):
    def __init__(self, combine_sites=True, prior_fn={}):
        super(LikelihoodPlotter, self).__init__(combine_sites, prior_fn)

    def visualize(self, calib_manager):
        iteration_status = calib_manager.status
        if iteration_status != ResumePoint.next_point:
            return  # Only plot once results are available

        self.all_results = calib_manager.all_results
        logger.debug(self.all_results)

        self.directory = calib_manager.iteration_directory()
        self.site_analyzer_names = calib_manager.site_analyzer_names()
        self.param_names = calib_manager.param_names()

        if self.combine_sites:
            self.plot_by_parameter()
        else:
            self.plot_by_parameter_and_site()

        # Data needed for the LL_CSV
        self.location = calib_manager.location
        self.iteration_state = calib_manager.iteration_state
        self.iteration = calib_manager.iteration
        self.comps_suite_id = calib_manager.comps_suite_id
        try:
            self.write_LL_csv(calib_manager.exp_manager.experiment)
        except:
            logger.info("Log likelihood CSV could not be created. Skipping...")

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

            plt.savefig(os.path.join(self.directory, site, 'LL_%s.pdf' % param), format='PDF')
            plt.close(fig)

    def plot1d_by_iteration(self, results, param, total, **kwargs):
        iterations = results.reset_index().groupby('iteration', sort=True)
        n_iterations = len(iterations)

        colors = ['#4BB5C1'] * (n_iterations - 1) + ['#FF2D00']

        for iter, values in iterations:
            sorted_values = values.sort_values(by=param)
            plt.plot(sorted_values[param], sorted_values[total],
                     color=colors[int(iter)],
                     linewidth=(iter + 1) / (n_iterations + 1.) * 2,
                     alpha=(iter + 1) / (n_iterations + 1.),
                     **kwargs)

    def cleanup_plot(self, calib_manager):
        """
        cleanup the existing plots
        :param calib_manager:
        :return:
        """
        self.directory = calib_manager.iteration_directory()
        self.param_names = calib_manager.param_names()
        self.site_analyzer_names = calib_manager.site_analyzer_names()

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

    def write_LL_csv(self, experiment):
        """
        Write the LL_summary.csv with what is in the CalibManager
        """
        # DJK: RENAME LL everywhere.  It's whatever the analyzer(s) return, e.g. cost per life saved
        # DJK: That brings up an interesting issue about how to combine analyzers results.  For now, we sum.
        #      But that might not be sufficiently general - think about this.

        # Deep copy all_results and pnames to not disturb the calibration
        pnames = copy.deepcopy(self.param_names)
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
            sims_paths = CompsDTKOutputParser.createSimDirectoryMap(suite_id=self.comps_suite_id, save=False)
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