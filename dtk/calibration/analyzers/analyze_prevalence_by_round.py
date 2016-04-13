# Template script for analyzing and visualizing simulation output from calibtool
#
# Replace all instances of TEMPLATE with new analyzer name.
# Replace all instances of DATATYPE with data descriptor
#
#

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.ticker import FixedLocator
import pandas as pd
import json
import math
import seaborn as sns
import os

from dtk.calibration import LL_calculators
from dtk.calibration.study_sites.set_calibration_site import get_reference_data


def analyze_prevalence_by_round(settings, analyzer, site, data, samples) :

    LL_fn = getattr(LL_calculators, analyzer['LL_fn'])
    raw_data = get_reference_data(site, 'prevalence_by_round')
    
    if 'regions' not in analyzer :
        regions = ['all']
    else :
        regions = analyzer['regions']

    field = analyzer['fields_to_get'][0]
    LL = [0]*len(samples.index)

    record_data_by_sample = { 'prevalence_by_round' : {} }
    for region in regions :
        record_data_by_sample['prevalence_by_round'][region] = []
        for rownum in range(len(LL)) :

            mean_sim_data = [np.mean([data[y][region][field][rownum][x] for y in range(settings['sim_runs_per_param_set'])]) for x in analyzer['testdays']]

            LL[rownum] += LL_fn(raw_data[region], mean_sim_data)
            record_data_by_sample['prevalence_by_round'][region].append(mean_sim_data)

    with open(os.path.join(settings['curr_iteration_dir'],site + '_' + analyzer['name'] + '.json'), 'w') as fout :
        json.dump(record_data_by_sample, fout)
    return LL

def visualize_prevalence_by_round(settings, iteration, analyzer, site, samples, top_LL_index) :

    if 'regions' not in analyzer :
        regions = ['all']
    else :
        regions = analyzer['regions']
    for region in regions :
        plot_all_LL(settings, iteration, site, analyzer, samples, region)
        plot_best_LL(settings, iteration, site, analyzer, samples, top_LL_index, region)
    plot_all_LL(settings, iteration, site, analyzer, samples)

def plot_best_LL(settings, iteration, site, analyzer, samples, top_LL_index, region='all') :
        
    raw_data = get_reference_data(site, 'prevalence_by_round')[region]

    for j, LL_index in enumerate(top_LL_index) :
        fname = os.path.join(settings['plot_dir'], site + '_' + region + '_prevalence_by_round_LLrank' + str(j))
        sns.set_style('white')
        fig = plt.figure(fname, figsize=(4,3))
        plt.subplots_adjust(left=0.15, bottom=0.15, right=0.95)
        ax = fig.add_subplot(111)    

        iter = samples['iteration'].values[LL_index]
        prevsamples = len(samples[samples['iteration'] < iter].index)
        rownum = LL_index-prevsamples
        with open(os.path.join(settings['exp_dir'], 'iter' + str(iter) + '/' + site + '_' + analyzer['name']) + '.json') as fin :
            data = json.loads(fin.read())
        plot(ax, data['prevalence_by_round'][region][rownum], style='-o', color='#CB5FA4', alpha=1, linewidth=1)
        plot(ax, raw_data, style='-o', color='#8DC63F', alpha=1, linewidth=1)
        plt.savefig(fname + '.pdf', format='PDF')
        plt.close(fig)

def plot_all_LL(settings, iteration, site, analyzer, samples, region='all') :

    raw_data = get_reference_data(site, 'prevalence_by_round')[region]

    LL = samples['LL'].values
    LL_max = max(LL)
    LL_min = min(LL)
    if LL_min == LL_max : LL_min = LL_max-1

    fname = os.path.join(settings['plot_dir'], site + '_' + region + '_prevalence_by_round_all')
    sns.set_style('white')
    fig = plt.figure(fname, figsize=(4,3))
    plt.subplots_adjust(left=0.15, bottom=0.15, right=0.95)
    ax = fig.add_subplot(111)    

    grouped = samples.groupby('iteration')
    prevsamples = 0
    for i, (iter, df_iter) in enumerate(grouped) :
        with open(os.path.join(settings['exp_dir'], 'iter' + str(iter) + '/' + site + '_' + analyzer['name']) + '.json') as fin :
            data = json.loads(fin.read())['prevalence_by_round'][region]
        for rownum, sim_data in enumerate(data) :
            plot(ax, sim_data, style='-', color=cm.Blues((LL[rownum + prevsamples]-LL_min)/(LL_max-LL_min)), alpha=0.5, linewidth=0.5)
        prevsamples += len(df_iter.index)
    plot(ax, raw_data, style='-o', color='#8DC63F', alpha=1, linewidth=1)
    plt.savefig(fname + '.pdf', format='PDF')
    plt.close(fig)

def plot(ax, data, style='-o', color='#CB5FA4', alpha=0.5, linewidth=0.5) :

    ax.plot(range(len(data)), data, style, color=color, alpha=alpha, linewidth=linewidth) 
    ax.set_xticks(range(len(data)))
    ax.set_xticklabels([str(x+1) for x in range(len(data))])
    ax.set_xlabel('MSAT round')
    ax.set_ylabel('RDT prevalence')
    ax.set_xlim(-1, len(data))

    return
