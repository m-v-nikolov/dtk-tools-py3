import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from dtk.utils.analyzers.BaseTimeseriesAnalyzer import BaseTimeseriesAnalyzer

def example_filter(sim_metadata):
    #print(sim_metadata)
    return sim_metadata['Run_Number'] > 0

def example_selection(timeseries):
    # note this is once-per-week snapshots, not weekly (running) averages...
    weekly=timeseries[::7]
    dates=pd.date_range('1/1/2000', periods=len(weekly), freq='W')
    return pd.Series(weekly,index=dates)

def no_grouping(simid,metadata):
    #print(simid,metadata)
    return simid

def group_by_name(simid,metadata):
    #print(simid,metadata)
    return metadata.get('Config_Name',simid)

def group_all(simid,metadata):
    #print(simid,metadata)
    return 'all'

def no_plots(d,ax):
    pass

def plot_with_tsplot(d,ax):
    # This is a bit slower than just using standard deviations (probably on account of bootstrap confidence intervals?)
    # Also an issue with the tsplot keyword argument'time': as(float) instead of datetime? https://github.com/mwaskom/seaborn/issues/242
    groups=d.keys().levels[0]
    n_groups=len(groups)
    values=d.values
    shape=[-1,n_groups,values.shape[1]/n_groups]
    reshaped=np.reshape(values,shape)
    cube=np.transpose(reshaped,(2,0,1)) # samples,timepoints,groups
    sns.tsplot(cube,condition=pd.Series(groups,name='site'),err_style='ci_band',ci=np.linspace(95, 10, 4),time=d.index)

def plot_CI_bands(d,ax):
    grouped = d.groupby(level=['group'], axis=1)
    m=grouped.mean()
    m.plot(ax=ax,legend=True)
    s=grouped.std()
    palette=sns.color_palette()
    for n_std in [2,1]:
        lower_ci,upper_ci=m-n_std*s,m+n_std*s
        for i,g in enumerate(m.keys()):
            plt.fill_between(d.index,lower_ci[g],upper_ci[g],alpha=0.1,color=palette[i%len(palette)])
            plt.fill_between(d.index,lower_ci[g],upper_ci[g],alpha=0.1,color=palette[i%len(palette)])

analyzers = [ BaseTimeseriesAnalyzer(
                #filter_function=example_filter,
                select_function=example_selection,
                group_function=group_all,
                plot_function=plot_CI_bands)
            ]