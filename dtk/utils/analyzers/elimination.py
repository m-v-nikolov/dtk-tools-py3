import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from .timeseries import TimeseriesAnalyzer

def default_scatter_fn(df,ax):
    print(df)
    df.plot(kind='scatter',
            x='scale',y='coverage', 
            c='eliminated', cmap='afmhot',
            s=200, ax=ax, vmin=0, vmax=1)

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
        fig=plt.figure('EliminationPlots',figsize=(15,4))
        for i,d in enumerate(dd):
            ax=fig.add_subplot(1,len(dd),i+1)
            ax.set_title('Duration=%d'%d)
            s=df.loc[d]
            self.plot_function(s,ax)
        plt.tight_layout()

    def save(self):
        self.data.to_csv('elimination.csv')