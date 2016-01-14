# Template script for analyzing and visualizing simulation output from calibtool
#
# Replace all instances of TEMPLATE with new analyzer name.
# Replace all instances of DATATYPE with data descriptor
#
#
import os

import numpy as np
import LL_calculators
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.ticker import FixedLocator
import pandas as pd
import json
import math
import seaborn as sns
from study_sites.set_calibration_site import get_reference_data

def analyze_TEMPLATE(settings, analyzer, site, data, samples) :

    LL_fn = getattr(LL_calculators, analyzer['LL_fn'])
    raw_data = get_reference_data(site, 'DATATYPE')
    
    field = analyzer['fields_to_get'][0]
    LL = [0]*len(samples.index)

    record_data_by_sample = { 'DATATYPE' : [] }
    for rownum in range(len(LL)) :

        mean_sim_data = [np.mean([data[y][field][rownum][x] for y in range(settings['sim_runs_per_param_set'])]) for x in range(len(raw_data))]

        LL[rownum] += LL_fn(raw_data, mean_sim_data)
        record_data_by_sample['DATATYPE'].append(mean_sim_data)

    with open(settings['curr_iteration_dir'] + site + '_' + analyzer['name'] + '.json', 'w') as fout :
        json.dump(record_data_by_sample, fout)
    return LL

def visualize_TEMPLATE(settings, iteration, analyzer, site, samples, top_LL_index) :

    return
    plot_best_LL(settings, iteration, site, analyzer, samples, top_LL_index)
    plot_all_LL(settings, iteration, site, analyzer, samples)

def plot_best_LL(settings, iteration, site, analyzer, samples, top_LL_index) :
        
    raw_data = get_reference_data(site, 'DATATYPE')

    for j, LL_index in enumerate(top_LL_index) :
        fname = os.path.join(settings['plot_dir'], site + '_DATATYPE_LLrank' + str(j))
        sns.set_style('white')
        fig = plt.figure(fname, figsize=(4,3))
        plt.subplots_adjust(left=0.15, bottom=0.15, right=0.95)
        ax = fig.add_subplot(111)    

        iter = samples['iteration'].values[LL_index]
        prevsamples = len(samples[samples['iteration'] < iter].index)
        rownum = LL_index-prevsamples
        with open(settings['exp_dir'] + 'iter' + str(iter) + '/' + site + '_' + analyzer['name'] + '.json') as fin :
            data = json.loads(fin.read())
        plot(ax, data['DATATYPE'][rownum], style='-o', color='#CB5FA4', alpha=1, linewidth=1)
        plot(ax, raw_data, style='-o', color='#8DC63F', alpha=1, linewidth=1)
        plt.savefig(fname + '.pdf', format='PDF')
        plt.close(fig)


def plot_all_LL(settings, iteration, site, analyzer, samples) :

    raw_data = get_reference_data(site, 'DATATYPE')

    LL = samples['LL'].values
    LL_max = max(LL)
    LL_min = min(LL)
    if LL_min == LL_max : LL_min = LL_max-1

    fname = os.path.join(settings['plot_dir'], site + '_DATATYPE_all')
    sns.set_style('white')
    fig = plt.figure(fname, figsize=(4,3))
    plt.subplots_adjust(left=0.15, bottom=0.15, right=0.95)
    ax = fig.add_subplot(111)    

    grouped = samples.groupby('iteration')
    prevsamples = 0
    for i, (iter, df_iter) in enumerate(grouped) :
        with open(os.path.join(settings['exp_dir'],'iter' + str(iter) , site + '_' + analyzer['name'] + '.json')) as fin :
            data = json.loads(fin.read())['DATATYPE']
        for rownum, sim_data in enumerate(data) :
            plot(ax, sim_data, style='-', color=cm.Blues((LL[rownum + prevsamples]-LL_min)/(LL_max-LL_min)), alpha=0.5, linewidth=0.5)
        prevsamples += len(df_iter.index)
    plot(ax, raw_data, style='-o', color='#8DC63F', alpha=1, linewidth=1)
    plt.savefig(fname + '.pdf', format='PDF')
    plt.close(fig)

def plot(ax, data, style='-o', color='#CB5FA4', alpha=0.5, linewidth=0.5) :

    ax.plot(range(len(data)), data, style, color=color, alpha=alpha, linewidth=linewidth) 

    return
