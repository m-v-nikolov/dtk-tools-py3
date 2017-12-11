import matplotlib
matplotlib.use('Agg')
import logging
import operator
import os

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from calibtool.algorithms.PBnB.c_SubRegion import c_SubRegion
from calibtool.plotters.BasePlotter import BasePlotter

logger = logging.getLogger(__name__)

sns.set_style('white')


class OptimToolPBnBPlotter(BasePlotter):
    def __init__(self):
        super(OptimToolPBnBPlotter, self).__init__( False )

    def cleanup(self):
        pass

    def plot_state_evolution(self, **kwargs):
        data = kwargs.pop('data')
        all_it = data['Iteration'].astype(int)

        dynamic = data.query('Dynamic == True')
        static = data.query('Dynamic == False')

        plt.plot(all_it, data['Center'], color='k', marker=None)
        plt.plot(dynamic['Iteration'].astype(int), dynamic['Center'], 'ko', zorder=100)
        plt.plot(static['Iteration'].astype(int), static['Center'], color='0.75', marker='o', zorder=100)
        plt.plot(all_it, data['Min'], color='r')
        plt.plot(all_it, data['Max'], color='r')

        plt.margins(0.05)
        plt.autoscale(tight=False)

    def visualize(self, iteration_state):
        self.iteration_state = iteration_state


        self.directory = self.iteration_state.iteration_directory
        self.param_names = self.iteration_state.param_names
        self.site_analyzer_names = self.iteration_state.site_analyzer_names

        self.npt = self.iteration_state.next_point_algo.get_state()

        self.params = self.npt['params']
        self.str_k = str(self.npt['i_k'])
        self.l_subr = []
        for c_subr in self.npt['l_subr']:
            c_subr_set = c_SubRegion(self.npt['l_subr'][c_subr]['l_coordinate_lower'], self.npt['l_subr'][c_subr]['l_coordinate_upper'], self.params)
            c_subr_set.i_index = self.npt['l_subr'][c_subr]['i_index']
            c_subr_set.s_label = self.npt['l_subr'][c_subr]['s_label']
            c_subr_set.b_activate = self.npt['l_subr'][c_subr]['b_activate']
            c_subr_set.b_branchable = self.npt['l_subr'][c_subr]['b_branchable']
            c_subr_set.b_elite = self.npt['l_subr'][c_subr]['b_elite']
            c_subr_set.b_worst = self.npt['l_subr'][c_subr]['b_worst']
            c_subr_set.b_maintaining_indicator = self.npt['l_subr'][c_subr]['b_maintaining_indicator']
            c_subr_set.b_pruning_indicator = self.npt['l_subr'][c_subr]['b_pruning_indicator']
            c_subr_set.f_volume = self.npt['l_subr'][c_subr]['f_volume']
            c_subr_set.i_min_sample = self.npt['l_subr'][c_subr]['i_min_sample']
            c_subr_set.i_max_sample = self.npt['l_subr'][c_subr]['i_max_sample']
            c_subr_set.f_min_diff_sample_mean = self.npt['l_subr'][c_subr]['f_min_diff_sample_mean']
            c_subr_set.f_max_var = self.npt['l_subr'][c_subr]['f_max_var']
            c_subr_set.pd_sample_record = pd.DataFrame.from_dict(self.npt['l_subr'][c_subr]['pd_sample_record'], orient='columns')
            c_subr_set.pd_sample_record['rep'].astype(int)
            self.l_subr.append(c_subr_set)
        self.l_subr.sort(key=operator.attrgetter('i_index'))  # dinc->list and sorting

        self.l_ini_coordinate_lower = self.l_subr[0].l_coordinate_lower
        self.l_ini_coordinate_upper = self.l_subr[0].l_coordinate_upper
        self.visualize_results()


        ###gc.collect()


    def visualize_results(self):

        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.plot(self.l_ini_coordinate_upper[0], self.l_ini_coordinate_upper[1])
        ax.plot(self.l_ini_coordinate_lower[0], self.l_ini_coordinate_lower[1])

        for c_subr in (c_subr for c_subr in self.l_subr if c_subr.b_activate is True):
            if c_subr.s_label == 'M':
                alpha_value = 1
            elif c_subr.s_label == 'P':
                alpha_value = 0.1
            else:  # i.s_label == 'C':
                alpha_value = 0.6
            ax.add_patch(
                patches.Rectangle(
                    (c_subr.l_coordinate_lower[0], c_subr.l_coordinate_lower[1]),  # (x,y)
                    c_subr.l_coordinate_upper[0] - c_subr.l_coordinate_lower[0],  # width
                    c_subr.l_coordinate_upper[1] - c_subr.l_coordinate_lower[1],  # height
                    alpha=alpha_value,
                    edgecolor="black"
                )
            )
        # the following plot the minimum and maximum point
        df_all_sample = pd.concat([c_subr.pd_sample_record for c_subr in self.l_subr if c_subr.b_activate is True])
        df_all_sample = df_all_sample.sort_values(by="mean", ascending=True)  # sort before start
        df_all_sample = df_all_sample.reset_index(drop=True)
        f_min_value = df_all_sample.loc[0, 'mean']
        f_max_value = df_all_sample.loc[len(df_all_sample) - 1, 'mean']
        l_min_coordinate = [df_all_sample.loc[0, p['Name']] for p in self.params]
        l_max_coordinate = [df_all_sample.loc[len(df_all_sample) - 1, p['Name']] for p in self.params]
        p_min, p_max = ax.plot(l_min_coordinate[0], l_min_coordinate[1], '*b', l_max_coordinate[0], l_max_coordinate[1],
                               'or')
        fig.legend((p_min, p_max), (
        'minimum point:[' + str(l_min_coordinate[0]) + ',' + str(l_min_coordinate[1]) + '], result:' + str(f_min_value),
        'maximum point:[' + str(l_max_coordinate[0]) + ',' + str(l_max_coordinate[1]) + '], result:' + str(
            f_max_value)), 'upper right')


        for c_subr in (c_subr for c_subr in self.l_subr if c_subr.b_activate is True):
            ax.text(float(c_subr.l_coordinate_lower[0] + c_subr.l_coordinate_upper[0]) / 2, float(c_subr.l_coordinate_lower[1] + c_subr.l_coordinate_upper[1]) / 2,
                    str(c_subr.pd_sample_record['rep'].sum()))
        # plt.legend(handles=[red_patch, blue_patch])
        i_total_simulation = 0
        for c_subr in (c_subr for c_subr in self.l_subr if c_subr.b_activate is True):
            i_total_simulation += (c_subr.pd_sample_record['rep'].sum())
        fig.text(0.02, 0.02, 'total number of simulation:'+str(i_total_simulation), fontsize=14)

        ax.set_xlabel([p['Name'] for p in self.params][0])
        ax.set_ylabel([p['Name'] for p in self.params][1])



        fig.savefig(os.path.join(self.directory, 'Region_Status ' + self.str_k + '.pdf'))
        plt.close(fig)

