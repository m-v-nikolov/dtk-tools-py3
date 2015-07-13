from collections import namedtuple

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
import pandas as pd
import statsmodels.nonparametric.api as nparam
import seaborn as sns

from .timeseries import TimeseriesAnalyzer
from .group import group_by_name, combo_group

FacetPoint = namedtuple('FacetPoint', ['x', 'y', 'row', 'col'])
Ranges = namedtuple('Ranges', ['x', 'y', 'z'])

def interp_scatter(x, y, z, ranges, cmap='afmhot', **kwargs):
    xlim, ylim, (vmin, vmax) = ranges

    model = nparam.KernelReg([z], [x, y], reg_type='ll', var_type='cc', bw='cv_ls')
    X, Y = np.mgrid[slice(xlim[0], xlim[1], 100j), slice(ylim[0], ylim[1], 100j)]
    positions = np.vstack([X.ravel(), Y.ravel()]).T
    sm_mean, sm_mfx = model.fit(positions)
    Z = np.reshape(sm_mean, X.shape)

    color_args=dict(cmap=cmap, vmin=vmin, vmax=vmax, alpha=1)
    im = plt.pcolormesh(X, Y, Z, shading='gouraud', **color_args)
            
    kwargs.update(color_args)
    plt.scatter(x, y, s=20, c=z, lw=0.5, edgecolor='darkgray', **kwargs)
    plt.gca().set(xlim=xlim, ylim=ylim)

class EliminationAnalyzer(TimeseriesAnalyzer):

    plot_name = 'EliminationPlots'
    output_file = 'elimination.csv'

    def __init__(self, x, y, row=None, col=None, extra_metadata=[],
                 filter_function = lambda md: True,
                 select_function = lambda ts: pd.Series(ts[-1] == 0, index=['probability eliminated']),
                 xlim=(0, 1), ylim=(0, 1), zlim=(0, 1), cmap='afmhot',
                 channels=['Infected'], saveOutput=True):

        self.facet_point = FacetPoint(x, y, row, col)
        self.metadata = [p for p in self.facet_point if p] + extra_metadata
        self.ranges = Ranges(xlim, ylim, zlim)
        self.cmap = cmap

        group_function = combo_group(*[group_by_name(p) for p in self.metadata])

        TimeseriesAnalyzer.__init__(self, 'InsetChart.json',
                                    filter_function, select_function,
                                    group_function, plot_function=None,
                                    channels=channels, saveOutput=saveOutput)

    def plot(self):
        x, y, row, col = self.facet_point
        self.df.sort([v for v in [row, col] if v], inplace=True)
        g = sns.FacetGrid(self.df, col=col, row=row, margin_titles=True, size=4.5, aspect=1.2)

        g.map(interp_scatter, x, y, self.outcome, ranges=self.ranges, cmap=self.cmap)\
         .fig.subplots_adjust(wspace=0.1, hspace=0.05, right=0.85)
                
        cax = plt.gcf().add_axes([0.9, 0.1, 0.02, 0.8])
        cb = plt.colorbar(cax=cax)
        cb.ax.set_ylabel(self.outcome, rotation=270)
        cb.ax.get_yaxis().labelpad = 25

    def finalize(self):
        self.df = self.data.groupby(level=['group', 'sim_id'], axis=1).mean()
        self.outcome = self.df.index[0]
        self.df = self.df.stack(['group', 'sim_id']).unstack(0).reset_index()
        for n, col in enumerate(self.metadata):
            if col in self.df.columns:
                print('WARNING: "%s" already in DataFrame. Probably derived quantity rather than simulation metadata.' % col)
                continue
            self.df[col] = self.df['group'].apply(lambda g: g[n])
        self.df = self.df.drop('group', axis=1).set_index('sim_id')

        self.plot()

        if self.saveOutput:
            plt.savefig(self.plot_name + '.pdf', format='pdf')
            self.df.to_csv(self.output_file)