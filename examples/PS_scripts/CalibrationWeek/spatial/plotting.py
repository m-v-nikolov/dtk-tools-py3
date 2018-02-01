import calendar
import datetime
import os
import logging

import matplotlib.pyplot as plt
import pandas as pd

log = logging.getLogger(__name__)


def cmaps_config(df):
    df['date'] = df.date.apply(lambda x: pd.to_datetime(x).strftime('%m/%Y'))
    dates = df['date'].unique()
    cmaps = {}
    cmaps.update({'%s' % s: 'RdYlGn' for s in dates})

    return cmaps, dates


def plot_HH_maps(cmpd_df, savedir, x='coordinates_lat', y='coordinates_lng', channels=['gambiae_count', 'funestus_count'], savefigs=True):

    cmaps, dates = cmaps_config(cmpd_df)

    fig, axs = plt.subplots(1, 2, figsize=(12, 6), sharex=True, sharey=True)

    for date in dates:
        for i, channel in enumerate(channels):

            df = cmpd_df[cmpd_df['date'] == date]

            axs[i].scatter(
                df[x], df[y],
                cmap=cmaps.get(date, 'viridis'),
                lw=0, s=10*cmpd_df[channel], alpha=0.5
            )
            axs[i].set_title(channel.split('_')[0])

        xlim = cmpd_df[x].min(), cmpd_df[x].max()
        ylim = cmpd_df[y].min(), cmpd_df[y].max()

        for ax in axs:
            ax.set(aspect='equal',
                   xticks=[], yticks=[],
                   xlabel='', ylabel='',
                   xlim=xlim, ylim=ylim)

        fig.set_tight_layout(True)

        if savefigs:
            if not os.path.exists('figures'):
                os.mkdir('figures')
            month = datetime.datetime.strptime(date, "%m/%Y").month
            year = datetime.datetime.strptime(date, "%m/%Y").year
            strdate = calendar.month_abbr[month]+ str(year)
            plt.savefig(os.path.join(savedir, 'figures_'+ strdate + '.png'))