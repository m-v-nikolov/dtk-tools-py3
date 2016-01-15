# Template script for analyzing and visualizing simulation output from calibtool
#
# Replace all instances of TEMPLATE with new analyzer name.
# Replace all instances of DATATYPE with data descriptor
#
#
import os

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.ticker import FixedLocator
import pandas as pd
import json
import math
import seaborn as sns

from dtk.tools.calibration.calibtool import LL_calculators
from dtk.tools.calibration.calibtool.study_sites.set_calibration_site import get_reference_data


def analyze_malariatherapy_duration(settings, analyzer, site, data, samples) :

    LL_fn = getattr(LL_calculators, analyzer['LL_fn'])
    raw_data = get_reference_data(site, 'density_timecourse')
    duration_bins = raw_data['infection_duration_bins']
    
    fields = analyzer['fields_to_get']
    LL = [0]*len(samples.index)

    record_data_by_sample = { 'duration' : {} }
    for field in fields :
        record_data_by_sample['duration'][field] = []

    for rownum in range(len(LL)) :
        for field in fields :
            partype = field.split('_')[-1][:-1]

            sim_data = []
            for y in range(settings['sim_runs_per_param_set']) :
                durs = get_durations(data[y][rownum], duration_bins, field, detection=10)    
                sim_data.append(durs)
            mean_sim_data = [np.mean([sim_data[y][x] for y in range(settings['sim_runs_per_param_set'])]) for x in range(len(duration_bins))]
            LL[rownum] += LL_fn(raw_data[partype + 'mia_durations'], mean_sim_data)
            record_data_by_sample['duration'][field].append(mean_sim_data)

    with open(os.path.join(settings['curr_iteration_dir'], site + '_' + analyzer['name'] + '.json'), 'w') as fout :
        json.dump(record_data_by_sample, fout)
    return LL

def visualize_malariatherapy_duration(settings, iteration, analyzer, site, samples, top_LL_index) :

    plot_best_LL(settings, iteration, site, analyzer, samples, top_LL_index)
    plot_all_LL(settings, iteration, site, analyzer, samples)

def plot_best_LL(settings, iteration, site, analyzer, samples, top_LL_index) :
        
    raw_data = get_reference_data(site, 'density_timecourse')
    duration_bins = raw_data['infection_duration_bins']
    fields = analyzer['fields_to_get']

    for j, LL_index in enumerate(top_LL_index) :
        fname = os.path.join(settings['plot_dir'], site + '_duration_LLrank' + str(j))
        sns.set_style('white')
        fig = plt.figure(fname, figsize=(6,len(fields)*3))
        plt.subplots_adjust(left=0.15, bottom=0.15, right=0.95, hspace=0.5)
        for f, field in enumerate(fields) :
            partype = field.split('_')[-1][:-1]
            ax = fig.add_subplot(len(fields), 1, f+1)    

            iter = samples['iteration'].values[LL_index]
            prevsamples = len(samples[samples['iteration'] < iter].index)
            rownum = LL_index-prevsamples
            with open(os.path.join(settings['exp_dir'],'iter' + str(iter), site + '_' + analyzer['name'] + '.json')) as fin :
                data = json.loads(fin.read())['duration']
            plot(ax, duration_bins, data[field][rownum], style='-o', color='#CB5FA4', alpha=1, linewidth=1)
            plot(ax, duration_bins, raw_data[partype + 'mia_durations'], style='-o', color='#8DC63F', alpha=1, linewidth=1)
            ax.set_xlabel(partype + 'mia duration (days)')
        plt.savefig(fname + '.pdf', format='PDF')
        plt.close(fig)


def plot_all_LL(settings, iteration, site, analyzer, samples) :

    raw_data = get_reference_data(site, 'density_timecourse')
    duration_bins = raw_data['infection_duration_bins']
    fields = analyzer['fields_to_get']

    LL = samples['LL'].values
    LL_max = max(LL)
    LL_min = min(LL)
    if LL_min == LL_max : LL_min = LL_max-1

    fname = os.path.join(settings['plot_dir'],site + '_duration_all')
    sns.set_style('white')
    fig = plt.figure(fname, figsize=(6,len(fields)*3))
    plt.subplots_adjust(left=0.15, bottom=0.15, right=0.95, hspace=0.5)

    for f, field in enumerate(fields) :
        partype = field.split('_')[-1][:-1]
        ax = fig.add_subplot(len(fields), 1, f+1)    

        grouped = samples.groupby('iteration')
        prevsamples = 0
        for i, (iter, df_iter) in enumerate(grouped) :
            with open(os.path.join(settings['exp_dir'],'iter' + str(iter), site + '_' + analyzer['name'] + '.json')) as fin :
                data = json.loads(fin.read())['duration']
            for rownum, sim_data in enumerate(data[field]) :
                plot(ax, duration_bins, sim_data, style='-', color=cm.Blues((LL[rownum + prevsamples]-LL_min)/(LL_max-LL_min)), alpha=0.5, linewidth=0.5)
            prevsamples += len(df_iter.index)
        plot(ax, duration_bins, raw_data[partype + 'mia_durations'], style='-o', color='#8DC63F', alpha=1, linewidth=1)
        ax.set_xlabel(partype + 'mia duration (days)')
    plt.savefig(fname + '.pdf', format='PDF')
    plt.close(fig)

def plot(ax, bins, data, style='-o', color='#CB5FA4', alpha=0.5, linewidth=0.5) :

    ax.plot(bins, [1.*x/sum(data) for x in data], style, color=color, alpha=alpha, linewidth=linewidth) 
    ax.set_ylim(0,1)
    ax.set_ylabel('fraction of patients')
    return

def get_durations(data, bins, partype, detection=10) :

    binned_durs = [0.]*len(bins)

    for patient in data :
        num_time_pts = len(patient[partype])
        start = 0
        end = num_time_pts
        for i in range(num_time_pts) :
            if patient[partype][i] >= detection :
                start = i
                break
        for i in reversed(range(num_time_pts)) :
            if patient[partype][i] >= detection :
                end = i
                break
        dur = end - start
        for i, this_bin in enumerate(bins) :
            if dur < this_bin :
                binned_durs[i] += 1
                break
        
    return binned_durs