import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

### Plot functions ###
def no_plots(df, ax):
    pass

def plot_CI_bands(df, ax):
    '''
    Using seaborn.tsplot is slower than just using standard deviations,
    probably on account of bootstrap confidence intervals.
    Also, an issue with the tsplot keyword argument 'time'
    as(float) not datetime: https://github.com/mwaskom/seaborn/issues/242
    '''
    groups = df.keys().levels[0]
    n_groups = len(groups)
    values = df.values
    shape = [-1, n_groups, values.shape[1]/n_groups]
    reshaped = np.reshape(values, shape)
    cube = np.transpose(reshaped, (2, 0, 1)) # samples,timepoints,groups
    sns.tsplot(cube, condition=pd.Series(groups, name='group'),
               err_style='ci_band', ci=np.linspace(95, 10, 4), time=df.index)

def plot_std_bands(df, ax):
    grouped = df.groupby(level=['group'], axis=1)
    m = grouped.mean()
    m.plot(ax=ax, legend=True)
    s = grouped.std()
    palette = sns.color_palette()
    for n_std in [2, 1]:
        lower_ci, upper_ci = m-n_std*s, m+n_std*s
        for i, g in enumerate(m.keys()):
            color = palette[i % len(palette)]
            plt.fill_between(df.index, lower_ci[g], upper_ci[g],
                             alpha=0.1, color=color)

def plot_grouped_lines(df, ax):
    grouped = df.groupby(level=['group'], axis=1)
    palette = sns.color_palette()
    leg=[]
    for i, (g, dfg) in enumerate(grouped):
        color = palette[i % len(palette)]
        dfg.plot(ax=ax, legend=False, alpha=0.6, lw=1, color=[color]) #?
        leg.append(plt.Line2D((0, 1), (0, 0), color=color))
    plt.legend(leg, df.keys().levels[0].tolist(), title='group')

### Subplots by channel
def plot_by_channel(plot_name, channels, plot_fn):
    ncol = 1 + len(channels)/4
    nrow = int(np.ceil(float(len(channels)) / ncol))

    fig, axs = plt.subplots(num=plot_name, 
                            figsize=(min(8, 4*ncol), min(6, 3*nrow)), 
                            nrows=nrow, ncols=ncol, 
                            sharex=True)
    axs = np.array(axs) # for 1x1 case

    for (channel, ax) in zip(channels, axs.reshape(-1)):
        ax.set_title(channel)
        plot_fn(channel, ax)

    fig.set_tight_layout(True)