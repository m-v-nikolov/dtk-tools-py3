import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
import pandas as pd
import statsmodels.nonparametric.api as nparam

from .timeseries import TimeseriesAnalyzer

## TODO: generalize the functionality of this to be less custom to a specific example!!

def default_scatter_fn(df,ax):

    #channel='eliminated'
    channel='infectiondays'

    model=nparam.KernelReg([df[channel]],
                           [df.scale,df.coverage],
                           reg_type='ll',var_type='cc',bw='cv_ls')

    X, Y = np.mgrid[0:1:100j, 0.5:1:100j]
    positions = np.vstack([X.ravel(), Y.ravel()]).T
    sm_mean, sm_mfx = model.fit(positions)
    Z = np.reshape(sm_mean, X.shape)

    color_args=dict(cmap='afmhot', vmin=0, vmax=365, alpha=0.5) ###############

    im=ax.pcolor(X,Y,Z,**color_args)

    df.plot(kind='scatter',
            x='scale',y='coverage', 
            c=channel, s=10, ax=ax, **color_args)

class EliminationAnalyzer(TimeseriesAnalyzer):

    def __init__(self,
                 filter_function = lambda md: True, # no filtering based on metadata
                 select_function = lambda ts: pd.Series(ts[-730] == 0,index=['eliminated']),
                 group_function  = lambda k,v: k,   # group by unique simid-key from parser
                 plot_function   = default_scatter_fn,
                 saveOutput = False):

        TimeseriesAnalyzer.__init__(self,'InsetChart.json',
                                    filter_function,select_function,
                                    group_function,plot_function,
                                    ['Infected'],saveOutput)

    def finalize(self):
        df=self.data.groupby(level=['group'], axis=1).mean()
        df=df.stack('group').unstack(0).reset_index()
        new_col_list = ['coverage','duration','scale']
        for n,col in enumerate(new_col_list):
            df[col] = df['group'].apply(lambda g: g[n])
        df = df.drop('group',axis=1).set_index(['coverage','duration','scale'],drop=False)
        df=df.reorder_levels(['duration','coverage','scale'])
        dd=df.index.levels[0]
        fig=plt.figure('EliminationPlots',figsize=(17,4))
        ax=None
        for i,d in enumerate(dd):
            ax=fig.add_subplot(1,len(dd),i+1,sharex=ax,sharey=ax)
            ax.set_title('IVM duration = %dd'%d if d else 'No IVM')
            ax.set(xlim=[0,1],ylim=[0.5,1])
            s=df.loc[d]
            self.plot_function(s,ax)
        plt.tight_layout()

    def save(self):
        self.data.to_csv('elimination.csv')