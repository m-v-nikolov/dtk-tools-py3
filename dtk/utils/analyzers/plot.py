import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def no_plots(df,ax):
    pass

def plot_with_tsplot(df,ax):
    '''
    Using seaborn.tsplot is slower than just using standard deviations,
    probably on account of bootstrap confidence intervals.
    Also, an issue with the tsplot keyword argument 'time'
    as(float) not datetime: https://github.com/mwaskom/seaborn/issues/242
    '''
    groups=df.keys().levels[0]
    n_groups=len(groups)
    values=df.values
    shape=[-1,n_groups,values.shape[1]/n_groups]
    reshaped=np.reshape(values,shape)
    cube=np.transpose(reshaped,(2,0,1)) # samples,timepoints,groups
    sns.tsplot(cube,condition=pd.Series(groups,name='site'),err_style='ci_band',ci=np.linspace(95, 10, 4),time=df.index)

def plot_CI_bands(df,ax):
    grouped = df.groupby(level=['group'], axis=1)
    m=grouped.mean()
    m.plot(ax=ax,legend=True)
    s=grouped.std()
    palette=sns.color_palette()
    for n_std in [2,1]:
        lower_ci,upper_ci=m-n_std*s,m+n_std*s
        for i,g in enumerate(m.keys()):
            color=palette[i%len(palette)]
            plt.fill_between(df.index,lower_ci[g],upper_ci[g],alpha=0.1,color=color)
            #plt.fill_between(df.index,lower_ci[g],upper_ci[g],alpha=0.1,color=palette[i%len(palette)])