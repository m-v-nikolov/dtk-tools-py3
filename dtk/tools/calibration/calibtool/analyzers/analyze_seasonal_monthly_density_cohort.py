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

def analyze_seasonal_monthly_density_cohort(settings, analyzer, site, data, samples) :

    LL_fn = getattr(LL_calculators, analyzer['LL_fn'])
    raw_data = get_reference_data(site, 'density_by_age_and_season')
    age_bins = raw_data['age_bins']
    density_bins = raw_data['parasitemia_bins']
    
    fields = analyzer['fields_to_get'][:2]
    LL = [0]*len(samples.index)

    record_data_by_sample = { 'density_by_age_and_season' : {} }
    for season in analyzer['seasons'] :
        record_data_by_sample['density_by_age_and_season'][season] = {}
        for field in fields :
            record_data_by_sample['density_by_age_and_season'][season][field] = []
    for rownum in range(len(LL)) :

        for field in fields :
            for season in analyzer['seasons'] :
                sim_data_all = []
                for y in range(settings['sim_runs_per_param_set']) :
                    row = data[y][field][rownum]
                    glom_every = range(analyzer['seasons'][season], len(row), 12)
                    sim_data = accumulate_agebins_cohort_2D(row, data[y]['Average Population by Age Bin'][rownum], 
                                                            age_bins, glom_every, 12)
                    sim_data_all.append(sim_data)
                sim_data = [[np.mean([sim_data_all[y][x][z] for y in range(settings['sim_runs_per_param_set'])]) for z in range(len(density_bins))] for x in range(len(age_bins))]
                LL[rownum] += LL_fn(np.array(raw_data[season][field]), np.array(sim_data))

                record_data_by_sample['density_by_age_and_season'][season][field].append(sim_data)

    with open(os.path.join(settings['curr_iteration_dir'], site + '_' + analyzer['name'] + '.json'), 'w') as fout :
        json.dump(record_data_by_sample, fout)
    return LL

def visualize_seasonal_monthly_density_cohort(settings, iteration, analyzer, site, samples, top_LL_index) :

    plot_best_LL(settings, iteration, site, analyzer, samples, top_LL_index)
    plot_all_LL(settings, iteration, site, analyzer, samples)

def plot_best_LL(settings, iteration, site, analyzer, samples, top_LL_index) :
        
    raw_data = get_reference_data(site, 'density_by_age_and_season')
    age_bins = raw_data['age_bins']
    density_bins = raw_data['parasitemia_bins']
    density_bins[0] = 0.5
    fields = analyzer['fields_to_get'][:2]
    seasons = analyzer['seasons'].keys()

    for j, LL_index in enumerate(top_LL_index) :

        iter = samples['iteration'].values[LL_index]
        prevsamples = len(samples[samples['iteration'] < iter].index)
        rownum = LL_index-prevsamples
        with open(settings['exp_dir'] + 'iter' + str(iter) + '/' + site + '_' + analyzer['name'] + '.json') as fin :
            data = json.loads(fin.read())['density_by_age_and_season']

        fname = os.path.join(settings['plot_dir'],site + '_density_by_age_and_season_LLrank' + str(j))
        sns.set_style('white')
        fig = plt.figure(fname, figsize=(len(seasons)*4,len(fields)*3))
        plt.subplots_adjust(left=0.15, bottom=0.15, right=0.95)
        for f, field in enumerate(fields) :
            for s, season in enumerate(seasons) :
                ax = fig.add_subplot(len(fields), len(seasons), f*len(seasons) + s + 1)    
                plot_bubbles(ax, np.array(data[season][field][rownum]), age_bins, density_bins, color='#CB5FA4')
                plot_bubbles(ax, np.array(raw_data[season][field]), age_bins, density_bins, color='#8DC63F')
                if s == 0 :
                    ax.set_ylabel(field.split()[2] + ' density')
                    ax.set_yticklabels(['none'] + ['<' + str(x) for x in density_bins[1:]])
                if f == 1 :
                    ax.set_xlabel('age in years')
                if f == 0 :
                    ax.set_title(season)

        plt.savefig(fname + '.pdf', format='PDF')
        plt.close(fig)

def plot_all_LL(settings, iteration, site, analyzer, samples) :

    raw_data = get_reference_data(site, 'density_by_age_and_season')
    age_bins = raw_data['age_bins']
    density_bins = raw_data['parasitemia_bins']
    density_bins[0] = 0.5
    fields = analyzer['fields_to_get'][:2]
    seasons = analyzer['seasons'].keys()

    LL = samples['LL'].values
    LL_max = max(LL)
    LL_min = min(LL)
    if LL_min == LL_max : LL_min = LL_max-1

    for f, field in enumerate(fields) :
        fname = os.path.join(settings['plot_dir'], site + '_' + field.split()[2] + '_density_by_age_and_season_all')
        sns.set_style('white')
        fig = plt.figure(fname, figsize=(len(seasons)*4,len(fields)*3))
        plt.subplots_adjust(left=0.15, bottom=0.15, right=0.95)

        grouped = samples.groupby('iteration')
        for a, age in enumerate(age_bins) :
            for s, season in enumerate(seasons) :
                ax = fig.add_subplot(len(age_bins), len(seasons), a*len(seasons) + s + 1)    
                prevsamples = 0
                for i, (iter, df_iter) in enumerate(grouped) :
                    with open(os.path.join(settings['exp_dir'],'iter' + str(iter),site + '_' + analyzer['name'] + '.json')) as fin :
                        data = json.loads(fin.read())['density_by_age_and_season']
                    for rownum, sim_data in enumerate(data[season][field]) :
                        plot(ax, density_bins, sim_data[a], style='-', color=cm.Blues((LL[rownum + prevsamples]-LL_min)/(LL_max-LL_min)), alpha=0.5, linewidth=0.5)
                    prevsamples += len(df_iter.index)
                plot(ax, density_bins, raw_data[season][field][a], style='-o', color='#8DC63F', alpha=1, linewidth=1)
                ax.set_xscale('log')
                ax.set_ylim(0,1)
                ax.set_xlim(10**-1, 10**7)
                ax.set_title(season + ' age <' + str(age))
                if s != 0 :
                    ax.set_yticklabels([])
                else :
                    ax.set_ylabel('fraction of age group')
                if a != len(age_bins)-1 :
                    ax.set_xticklabels([])
                else :
                    ax.set_xlabel(field.split()[2] + ' density per uL')
        plt.savefig(fname + '.pdf', format='PDF')
        plt.close(fig)

def plot(ax, bins, data, style='-o', color='#CB5FA4', alpha=0.5, linewidth=0.5) :

    ax.plot(bins, [1.*x/sum(data) for x in data], style, color=color, alpha=alpha, linewidth=linewidth) 

def plot_bubbles(ax, data, age_bins, density_bins, color='#CB5FA4') :

    for j in range(len(age_bins)) :
        for k in range(len(density_bins)-1) :
            ax.semilogy(j, density_bins[k], 'o', markersize=50*math.sqrt(1.*data[j, k]/(sum(data[j, :]))), 
                        markerfacecolor=color, alpha=0.5, linewidth=0)

    ax.set_ylim(10**-1, 10**7)
    ax.set_xlim(-1, 3)
    ax.xaxis.set_major_locator(FixedLocator(range(len(age_bins))))
    ax.set_xticklabels(['<' + str(age) for age in age_bins])
    ax.yaxis.set_major_locator(FixedLocator(density_bins))            
            
def insert_zeros(total_pop, data) :
    
    num_age_bins = len(data[:, 0])
    num_cat_bins = len(data[0, :])

    new_data = np.zeros((num_age_bins, num_cat_bins+1))
    for agebin in range(num_age_bins) :
        new_data[agebin, 0] = int(total_pop[agebin] - sum(data[agebin, :]))/total_pop[agebin]
        for catbin in range(num_cat_bins) :
            new_data[agebin, catbin+1] = int(data[agebin, catbin])#/total_pop[agebin]

    return new_data

def accumulate_agebins_cohort_2D(data, average_pop, agebins, glom_every=[], modifier=1) :

    if glom_every == [] and modifier == 1 :
        glom_every = range(len(data))

    agebins = [modifier * x for x in agebins]
    glommed_data = np.zeros((len(agebins), len(data[0])))
    ageindex = [0]*len(data)
    num_in_bin = [0]*len(agebins)
    for i in range(len(ageindex)) :
        for j, age in enumerate(agebins) :
            if i < age :
                ageindex[i] = j
                if i in glom_every :
                    num_in_bin[j] += average_pop[i][0]
                break

    for i in range(len(data)) :
        if i in glom_every :
            for j in range(len(data[i])) :
                glommed_data[ageindex[i], j] += data[i][j][0]*average_pop[i][0]

    return insert_zeros(num_in_bin, glommed_data)