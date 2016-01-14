# Template script for analyzing and visualizing simulation output from calibtool
#
# Replace all instances of TEMPLATE with new analyzer name.
# Replace all instances of DATATYPE with data descriptor
#
#
import os

import numpy as np
import dtk.tools.calibration.calibtool.LL_calculators
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.ticker import FixedLocator
import pandas as pd
import json
import math
import seaborn as sns
from study_sites.set_calibration_site import get_reference_data

def analyze_malariatherapy_density(settings, analyzer, site, data, samples) :

    LL_fn = getattr(LL_calculators, analyzer['LL_fn'])
    raw_data = get_reference_data(site, 'density_timecourse')
    density_bins = raw_data['parasitemia_bins']
    
    fields = analyzer['fields_to_get']
    LL = [0]*len(samples.index)

    record_data_by_sample = { 'peak_density' : {} }
    for field in fields :
        record_data_by_sample['peak_density'][field] = []

    for rownum in range(len(LL)) :
        for field in fields :
            partype = field.split('_')[-1][:-1]

            sim_data = []
            for y in range(settings['sim_runs_per_param_set']) :
                peaks = get_peak_densities(data[y][rownum], density_bins, field)    
                sim_data.append(peaks)
            mean_sim_data = [np.mean([sim_data[y][x] for y in range(settings['sim_runs_per_param_set'])]) for x in range(len(density_bins))]
            LL[rownum] += LL_fn(raw_data['peak_' + partype + 'mias'], mean_sim_data)
            record_data_by_sample['peak_density'][field].append(mean_sim_data)

    with open(os.path.join(settings['curr_iteration_dir'],site + '_' + analyzer['name'] + '.json'), 'w') as fout :
        json.dump(record_data_by_sample, fout)
    return LL

def visualize_malariatherapy_density(settings, iteration, analyzer, site, samples, top_LL_index) :

    plot_best_LL(settings, iteration, site, analyzer, samples, top_LL_index)
    plot_all_LL(settings, iteration, site, analyzer, samples)

def plot_best_LL(settings, iteration, site, analyzer, samples, top_LL_index) :
        
    raw_data = get_reference_data(site, 'density_timecourse')
    density_bins = raw_data['parasitemia_bins']
    density_bins[-1] = 10**6
    fields = analyzer['fields_to_get']

    for j, LL_index in enumerate(top_LL_index) :
        fname = os.path.join(settings['plot_dir'],site + '_peak_density_LLrank' + str(j))
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
                data = json.loads(fin.read())['peak_density']
            plot(ax, density_bins, data[field][rownum], style='-o', color='#CB5FA4', alpha=1, linewidth=1)
            plot(ax, density_bins, raw_data['peak_' + partype + 'mias'], style='-o', color='#8DC63F', alpha=1, linewidth=1)
            ax.set_xlabel(partype + ' density')
        plt.savefig(fname + '.pdf', format='PDF')
        plt.close(fig)


def plot_all_LL(settings, iteration, site, analyzer, samples) :

    raw_data = get_reference_data(site, 'density_timecourse')
    density_bins = raw_data['parasitemia_bins']
    density_bins[-1] = 10**6
    fields = analyzer['fields_to_get']

    LL = samples['LL'].values
    LL_max = max(LL)
    LL_min = min(LL)
    if LL_min == LL_max : LL_min = LL_max-1

    fname = os.path.join(settings['plot_dir'],site+'_peak_density_all')
    sns.set_style('white')
    fig = plt.figure(fname, figsize=(6,len(fields)*3))
    plt.subplots_adjust(left=0.15, bottom=0.15, right=0.95, hspace=0.5)

    for f, field in enumerate(fields) :
        partype = field.split('_')[-1][:-1]
        ax = fig.add_subplot(len(fields), 1, f+1)    

        grouped = samples.groupby('iteration')
        prevsamples = 0
        for i, (iter, df_iter) in enumerate(grouped) :
            with open(os.path.join(settings['exp_dir'],'iter' + str(iter) , site + '_' + analyzer['name'] + '.json')) as fin :
                data = json.loads(fin.read())['peak_density']
            for rownum, sim_data in enumerate(data[field]) :
                plot(ax, density_bins, sim_data, style='-', color=cm.Blues((LL[rownum + prevsamples]-LL_min)/(LL_max-LL_min)), alpha=0.5, linewidth=0.5)
            prevsamples += len(df_iter.index)
        plot(ax, density_bins, raw_data['peak_' + partype + 'mias'], style='-o', color='#8DC63F', alpha=1, linewidth=1)
        ax.set_xlabel(partype + ' density')
    plt.savefig(fname + '.pdf', format='PDF')
    plt.close(fig)

def plot(ax, bins, data, style='-o', color='#CB5FA4', alpha=0.5, linewidth=0.5) :

    ax.plot(bins, [1.*x/sum(data) for x in data], style, color=color, alpha=alpha, linewidth=linewidth) 
    ax.set_ylim(0,1)
    ax.set_ylabel('fraction of patients')
    ax.set_xscale('log')
    ax.xaxis.set_major_locator(FixedLocator(bins))
    ax.set_xticklabels(['<1e' + str(int(math.log10(x))) for x in bins])
    return

def get_peak_densities(data, bins, partype) :

    binned_peaks = [0.]*len(bins)

    for patient in data :
        max_density = max(patient[partype])
        for i, this_bin in enumerate(bins) :
            if max_density < this_bin :
                binned_peaks[i] += 1
                break

    return binned_peaks