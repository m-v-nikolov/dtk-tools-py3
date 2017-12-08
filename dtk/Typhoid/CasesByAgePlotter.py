import logging
import os

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from calibtool.plotters.BasePlotter import BasePlotter
from calibtool.visualize import combine_by_site

sns.set_style('white')

logger = logging.getLogger(__name__)


class CasesByAgePlotter(BasePlotter):
    def __init__(self, combine_sites=True):
        super(CasesByAgePlotter, self).__init__(combine_sites)

        self.fig_ext = 'png'

    def visualize(self, iteration_state):
        print("CasesByAgePlotter::visualize")
        self.iteration_state = iteration_state
        self.site_analyzer_names = iteration_state.site_analyzer_names
        iteration_status = self.iteration_state.status

        self.directory = self.iteration_state.iteration_directory
        self.param_names = self.iteration_state.param_names
        self.site_analyzer_names = self.iteration_state.site_analyzer_names

        data_dict = self.iteration_state.analyzers['Santiago_Case Age Distribution']
        #print data_dict.keys() # ['result', 'Sim', 'reference', 'reference_years']
        data = pd.DataFrame.from_dict(data_dict['Sim'], orient='columns')

        reference = pd.DataFrame.from_dict(data_dict['reference'], orient='columns')

        print('REF:\n', reference.head())
        print('DATA:\n', data.head())

        # TODO:
        # * Error bars on barplot of data
        # * Color order by log likelihood
        # * legend

        nSamples = len(set(data['Sample'].values))
        # Sim.Cases
        data['Huh'] = data['Sim.Cases.Unscaled'] / data['Sim.Population'] * data['Acute (Inc)']
        ax = sns.pointplot(data=data.head(250), x='Age', y='Huh', hue='Sample', palette=sns.color_palette("coolwarm", nSamples), zorder=-100, dodge=True, join=True )
        ax.legend_.remove()

        ax = sns.barplot(x='Age', y='Ref.Cases', data=reference, color='#A9A9A9', ax=ax)
        plt.show()

        #h_points, l_points = g.axes.flat[0].get_legend_handles_labels()
        plt.tight_layout()
        plt.subplots_adjust(top=0.9)
        g.fig.suptitle('Cases by Age', fontsize=16)

        # Axis outside right
        #handles, labels = g.axes.flat[0].get_legend_handles_labels()    # Draw nice legend outside to the right
        #plt.legend([h_bar[0], h_points[0]], [l_bar[0], l_points[0]], bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)

        plt.savefig(os.path.join(self.directory, 'Cases by Age.' + self.fig_ext)); plt.close()
        print("CasesByAgePlotter::DONE")

    def cleanup_plot(self):
        """
        cleanup the existing plots
        :return:
        """
