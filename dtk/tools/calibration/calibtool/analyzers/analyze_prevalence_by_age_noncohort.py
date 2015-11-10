import numpy as np
import LL_calculators
from load_comparison_data import load_comparison_data
import matplotlib.pyplot as plt
import json
from parsers_malaria import get_site_data
from matplotlib.ticker import FixedLocator
import matplotlib.cm as cm
import pandas as pd

def analyze_prevalence_by_age_noncohort(settings, analyzer, site, data) :

    raw_data_all = load_comparison_data(settings, site, 'prevalence_by_age')
    age_bins = raw_data_all['age_bins']

    LL = [0]*len(data[0]['Average Population by Age Bin'])
    for field in analyzer['fields_to_get'] :
        if field == 'Average Population by Age Bin' :
            continue
        raw_data_field = [int(x) for x in fraction_to_number(raw_data_all['n_obs'], raw_data_all[field])]
        n_raw, raw_data = raw_data_all['n_obs'], raw_data_field
        for rownum in range(len(LL)) :
            sim_data = [np.mean([data[y][field][rownum][0][x] for y in range(settings['sim_runs_per_param_set'])]) for x in range(len(age_bins))]
            n_sim = [np.mean([data[y]['Average Population by Age Bin'][rownum][0][x] for y in range(settings['sim_runs_per_param_set'])]) for x in range(len(age_bins))]

            LL[rownum] += LL_calculators.beta_binomial(n_raw, n_sim, raw_data, sim_data)
    return LL

def visualize_prevalence_by_age_noncohort(settings, iteration, analyzer, site, samples, top_LL_index) :

    plot_best_LL(settings, iteration, site, analyzer, samples, top_LL_index)
    #plot_all_LL(settings, iteration, site, analyzer, samples)

def plot_all_LL(settings, iteration, site, analyzer, samples) :

    data = get_site_data(settings, {}, site, iteration)[analyzer['name']]
    raw_data = load_comparison_data(settings, site, 'prevalence_by_age')
    age_bins = raw_data['age_bins']
    channel = analyzer['fields_to_get'][0]

    LL = samples['LL'].values
    LL_max = max(LL)
    LL_min = min(LL)
    if LL_min == LL_max : LL_min = LL_max-1
    fname = settings['plot_dir'] + site + '_prevalence_all'

    fig = plt.figure(fname, figsize=(4,3))
    plt.subplots_adjust(left=0.15, bottom=0.15, right=0.95)

    for rownum in range(len(LL)) :
        ax = fig.add_subplot(111)

        data_by_run = []
        for run_num in range(settings['sim_runs_per_param_set']) :
            outpath = samples[site + ' outpath ' + str(run_num)].values[rownum]
            data_by_run.append(get_summary_report_data(outpath))

        data = [np.mean([data_by_run[y][channel][0][x] for y in range(settings['sim_runs_per_param_set'])]) for x in range(len(age_bins))]

        plot_prevalence(ax, data, age_bins, plotstyle='-', mycolor=cm.Blues((LL[rownum]-LL_min)/(LL_max-LL_min)), 
                        alpha=0.5, linewidth=0.5)
        plot_prevalence(ax, raw_data[channel], age_bins, mycolor='#8DC63F')
        ax.set_ylabel(channel)

    plt.savefig(fname + '.pdf', format='PDF')
    plt.close(fig)

def plot_best_LL(settings, iteration, site, analyzer, samples, top_LL_index) :

    channel = analyzer['fields_to_get'][0]
    raw_data = load_comparison_data(settings, site, 'prevalence_by_age')
    age_bins = raw_data['age_bins']

    for j, LL_index in enumerate(top_LL_index) :
        fname = settings['plot_dir'] + site + '_prevalence_LLrank' + str(j)
        fig = plt.figure(fname, figsize=(4,3))
        plt.subplots_adjust(left=0.15, bottom=0.15, right=0.95)
        data_by_run = []
        for run_num in range(settings['sim_runs_per_param_set']) :
            outpath = samples[site + ' outpath ' + str(run_num)].values[LL_index]
            data_by_run.append(get_summary_report_data(outpath))
        ax = fig.add_subplot(111)    
        data = [np.mean([data_by_run[y][channel][0][x] for y in range(settings['sim_runs_per_param_set'])]) for x in range(len(age_bins))]
        plot_prevalence(ax, data, age_bins, mycolor='#CB5FA4')
        ax.set_ylabel(channel)
        plot_prevalence(ax, raw_data[channel], age_bins, mycolor='#8DC63F')
        plt.savefig(fname + '.pdf', format='PDF')
        plt.close(fig)

    return

def plot_prevalence(ax, data, agebins, plotstyle='-o', mycolor='#C01E6C', alpha=1, linewidth=1) :

    ax.plot(range(len(agebins)), data, plotstyle, color=mycolor, alpha=alpha, linewidth=linewidth)
    ax.set_ylim(0,1)
    ax.xaxis.set_major_locator(FixedLocator(range(len(agebins))))
    ax.set_xticklabels(['<' + str(agebins[0])] + [str(agebins[x]) + '-' + str(agebins[x+1]) for x in range(len(agebins)-2)] + [str(agebins[-2]) + '+'])
    ax.set_xlabel('age in years')

def get_summary_report_data(outpath) :

    simfile = 'MalariaSummaryReport_Daily_Report.json'
    with open(outpath + '/output/' + simfile) as fin :
        return json.loads(fin.read())    

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

    empty_bins = [i for i in range(len(agebins)) if i not in ageindex]

    return num_in_bin, glommed_data, empty_bins
