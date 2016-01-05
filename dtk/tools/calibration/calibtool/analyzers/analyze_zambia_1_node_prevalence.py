import numpy as np
import LL_calculators
from load_comparison_data import load_comparison_data
import matplotlib.pyplot as plt
import json
from parsers_malaria import get_site_data
import matplotlib.cm as cm
import pandas as pd

def analyze_zambia_1_node_prevalence(settings, analyzer, site, data) :

    raw_data = load_comparison_data(settings, site, 'prevalence_by_round')
    burn_in = analyzer['burn_in']
    campaign_days = [x + burn_in*365 for x in raw_data['campaign_days']]

    LL = [0]*len(data[0]['New Diagnostic Prevalence'])
    for field in analyzer['fields_to_get'] :
        for rownum in range(len(LL)) :
            sim_data = [np.mean([data[y][field][rownum][x] for y in range(settings['sim_runs_per_param_set'])]) for x in campaign_days]
            LL[rownum] += LL_calculators.euclidean_distance(raw_data['prevalence'], sim_data)
    return LL

def visualize_zambia_1_node_prevalence(settings, iteration, analyzer, site, samples, top_LL_index) :

    plot_best_LL(settings, iteration, site, analyzer, samples, top_LL_index)
    plot_all_LL(settings, iteration, site, analyzer, samples)
    
def plot_all_LL(settings, iteration, site, analyzer, samples) :

    if settings['combine_site_likelihoods'] :
        LL = samples['LL'].values
    else :
        LL = samples['LL ' + site].values
    burn_in = analyzer['burn_in']
    start_plot = 5*365
    plot_time = 3*365
    raw_data = load_comparison_data(settings, site, 'prevalence_by_round')

    channels = ['New Diagnostic Prevalence']
    numchannels = len(channels)

    LL_max = max(LL)
    LL_min = min(LL)
    if LL_min == LL_max : LL_min = LL_max-1
    fname = settings['plot_dir'] + site + '_prevalence_all'

    fig = plt.figure(fname, figsize=(4,numchannels*3))
    plt.subplots_adjust(left=0.15, bottom=0.15, right=0.95)
    data_by_run = get_site_data(settings, {}, site, iteration)[analyzer['name']]

    for i, channel in enumerate(channels) :
        ax = fig.add_subplot(numchannels, 1, i+1)

        for rownum in range(len(LL)) :
            data = [np.mean([data_by_run[y][channel][rownum][x+start_plot+burn_in*365] for y in range(settings['sim_runs_per_param_set'])]) for x in range(plot_time)]
            plot_prevalence(ax, data, range(plot_time), plotstyle='-', mycolor=cm.Blues((LL[rownum]-LL_min)/(LL_max-LL_min)), 
                            alpha=0.5, linewidth=0.5)
        if channel == 'New Diagnostic Prevalence' :
            plot_prevalence(ax, raw_data['prevalence'], [x-start_plot for x in raw_data['campaign_days']], ref=True, mycolor='#F9A11D')
        if i == numchannels-1 :
            ax.set_xlabel('age in years')
        ax.set_xlim(0,plot_time)

    plt.savefig(fname + '.pdf', format='PDF')
    plt.close(fig)

def plot_best_LL(settings, iteration, site, analyzer, samples, top_LL_index) :

    burn_in = analyzer['burn_in']
    start_plot = 5*365
    plot_time = 3*365
    raw_data = load_comparison_data(settings, site, 'prevalence_by_round')

    channels = ['New Diagnostic Prevalence']
    numchannels = len(channels)

    if iteration == 0 :
        fname = settings['plot_dir'] + site + '_reference_prevalence'
        fig = plt.figure(fname, figsize=(4,3))
        plt.subplots_adjust(left=0.15, bottom=0.15, right=0.95)
        for i, channel in enumerate(channels) :
            ax = fig.add_subplot(numchannels, 1, i+1)    
            plot_prevalence(ax, raw_data['prevalence'], [x-start_plot for x in raw_data['campaign_days']], ref=True, mycolor='#F9A11D')
            ax.set_ylabel(channel)
            if i == numchannels-1 :
                ax.set_xlabel('date')
            ax.set_xlim(0,plot_time)
        plt.savefig(fname + '.pdf', format='PDF')
        plt.close(fig)

    for j, LL_index in enumerate(top_LL_index) :
        fname = settings['plot_dir'] + site + '_prevalence_LLrank' + str(j)
        fig = plt.figure(fname, figsize=(4,3*numchannels))
        plt.subplots_adjust(left=0.15, bottom=0.15, right=0.95)
        data_by_run = []
        for run_num in range(settings['sim_runs_per_param_set']) :
            outpath = samples[site + ' outpath ' + str(run_num)].values[LL_index]
            data_by_run.append(get_inset_chart_data(outpath))
        for i, channel in enumerate(channels) :
            data = [np.mean([data_by_run[y][channel]['Data'][x+start_plot+burn_in*365] for y in range(settings['sim_runs_per_param_set'])]) for x in range(plot_time)]
            ax = fig.add_subplot(numchannels, 1, i+1)    
            plot_prevalence(ax, data, range(plot_time), plotstyle='-', mycolor='#C01E6C')
            ax.set_ylabel(channel)
            if i == numchannels-1 :
                ax.set_xlabel('date')
            if channel == 'New Diagnostic Prevalence' :
                plot_prevalence(ax, raw_data['prevalence'], [x-start_plot for x in raw_data['campaign_days']], ref=True, mycolor='#F9A11D')
            ax.set_xlim(0,plot_time)
        plt.savefig(fname + '.pdf', format='PDF')
        plt.close(fig)
    
    return

def plot_prevalence(ax, data, xloc, ref=False, plotstyle='o', mycolor='#C01E6C', alpha=1, linewidth=1) :

    ax.plot(xloc, data, plotstyle, color=mycolor, alpha=alpha, linewidth=linewidth)
    #ax.set_ylim(0,0.05)

def get_inset_chart_data(outpath) :

    simfile = 'InsetChart.json'
    with open(outpath + '/output/' + simfile) as fin :
        return json.loads(fin.read())['Channels'] 
