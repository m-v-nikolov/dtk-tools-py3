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

def analyze_prevalence_by_age_cohort(settings, analyzer, site, data, samples) :

    LL_fn = getattr(LL_calculators, analyzer['LL_fn'])
    raw_data_all = get_reference_data(site, 'prevalence_by_age')
    age_bins = raw_data_all['age_bins']
        
    field = analyzer['fields_to_get'][0]
    raw_data_field = [int(x) for x in fraction_to_number(raw_data_all['n_obs'], raw_data_all[field])]

    LL = [0]*len(samples.index)

    record_data_by_sample = { 'prevalence_by_age' : [] }
    for rownum in range(len(LL)) :

        n_sim = []
        sim_data = []
        for y in range(settings['sim_runs_per_param_set']) :

            n, k = accumulate_agebins_cohort([x[0] for x in data[y][field][rownum]], [x[0] for x in data[y]['Average Population by Age Bin'][rownum]], age_bins)
            n_sim.append(n)
            sim_data.append(k)

        n_sim = [np.mean([n_sim[y][x] for y in range(settings['sim_runs_per_param_set'])]) for x in range(len(age_bins))]
        sim_data = [np.mean([sim_data[y][x] for y in range(settings['sim_runs_per_param_set'])]) for x in range(len(age_bins))]
        empty_bins = [i for i in range(len(age_bins)) if n_sim[i] == 0]
        n_sim, sim_data = remove_empty_bins(n_sim, sim_data, empty_bins)
        n_raw, raw_data = remove_empty_bins(raw_data_all['n_obs'], raw_data_field, empty_bins)

        LL[rownum] += LL_fn(n_raw, n_sim, raw_data, sim_data)

        record_data_by_sample['prevalence_by_age'].append([sim_data[x]/n_sim[x] for x in range(len(n_sim))])

    record_data_by_sample['bins'] = [age_bins[i] for i in range(len(age_bins)) if i not in empty_bins]
    with open(os.path.join(settings['curr_iteration_dir'],site + '_' + analyzer['name'] + '.json'), 'w') as fout :
        json.dump(record_data_by_sample, fout)
    return LL

def visualize_prevalence_by_age_cohort(settings, iteration, analyzer, site, samples, top_LL_index) :

    plot_best_LL(settings, iteration, site, analyzer, samples, top_LL_index)
    plot_all_LL(settings, iteration, site, analyzer, samples)

def plot_best_LL(settings, iteration, site, analyzer, samples, top_LL_index) :
        
    raw_data_all = get_reference_data(site, 'prevalence_by_age')
    age_bins = raw_data_all['age_bins']
    field = analyzer['fields_to_get'][0]
    raw_data = raw_data_all[field]

    for j, LL_index in enumerate(top_LL_index) :
        fname = os.path.join(settings['plot_dir'],site + '_prevalence_by_age_LLrank' + str(j))
        sns.set_style('white')
        fig = plt.figure(fname, figsize=(4,3))
        plt.subplots_adjust(left=0.15, bottom=0.15, right=0.95)
        ax = fig.add_subplot(111)    

        iter = samples['iteration'].values[LL_index]
        prevsamples = len(samples[samples['iteration'] < iter].index)
        rownum = LL_index-prevsamples
        with open(os.path.join(settings['exp_dir'],'iter' + str(iter), site + '_' + analyzer['name'] + '.json')) as fin :
            data = json.loads(fin.read())
        plot(ax, data['bins'], data['prevalence_by_age'][rownum], style='-o', color='#CB5FA4', alpha=1, linewidth=1)
        plot(ax, age_bins, raw_data, style='-o', color='#8DC63F', alpha=1, linewidth=1)
        plt.savefig(fname + '.pdf', format='PDF')
        plt.close(fig)


def plot_all_LL(settings, iteration, site, analyzer, samples) :

    raw_data_all = get_reference_data(site, 'prevalence_by_age')
    age_bins = raw_data_all['age_bins']
    field = analyzer['fields_to_get'][0]
    raw_data = raw_data_all[field]

    LL = samples['LL'].values
    LL_max = max(LL)
    LL_min = min(LL)
    if LL_min == LL_max : LL_min = LL_max-1

    fname = os.path.join(settings['plot_dir'], site + '_prevalence_by_age_all')
    sns.set_style('white')
    fig = plt.figure(fname, figsize=(4,3))
    plt.subplots_adjust(left=0.15, bottom=0.15, right=0.95)
    ax = fig.add_subplot(111)    

    grouped = samples.groupby('iteration')
    prevsamples = 0
    for i, (iter, df_iter) in enumerate(grouped) :
        with open(os.path.join(settings['exp_dir'],'iter' + str(iter),site + '_' + analyzer['name'] + '.json')) as fin :
            data = json.loads(fin.read())
        for rownum, sim_data in enumerate(data['prevalence_by_age']) :
            plot(ax, data['bins'], sim_data, style='-', color=cm.Blues((LL[rownum + prevsamples]-LL_min)/(LL_max-LL_min)), alpha=0.5, linewidth=0.5)
        prevsamples += len(df_iter.index)
    plot(ax, age_bins, raw_data, style='-o', color='#8DC63F', alpha=1, linewidth=1)
    plt.savefig(fname + '.pdf', format='PDF')
    plt.close(fig)

def plot(ax, agebins, data, style='-o', color='#CB5FA4', alpha=0.5, linewidth=0.5) :

    ax.plot(agebins, data, style, color=color, alpha=alpha, linewidth=linewidth) 
    ax.set_ylim(0,0.3)
    ax.set_ylabel('Prevalence')
    ax.set_xlabel('age')
    return

def remove_empty_bins(n_obs, data, empty_bins) :

    n = [n_obs[i] for i in range(len(n_obs)) if i not in empty_bins]
    d = [data[i] for i in range(len(data)) if i not in empty_bins]

    return n, d

def fraction_to_number(n, f) :

    return [f[i]*n[i] for i in range(len(n))]

def accumulate_agebins_cohort(data, average_pop, agebins) :

    glommed_data = [0]*len(agebins)
    ageindex = [-1]*len(data)
    num_in_bin = [0]*len(agebins)
    for i in range(len(ageindex)) :
        for j, age in enumerate(agebins) :
            if i < age :
                ageindex[i] = j
                num_in_bin[j] += average_pop[i]
                break

    for i in range(len(ageindex)) :
        if ageindex[i] < 0 :
            continue
        glommed_data[ageindex[i]] += data[i]*average_pop[i]

    return num_in_bin, glommed_data