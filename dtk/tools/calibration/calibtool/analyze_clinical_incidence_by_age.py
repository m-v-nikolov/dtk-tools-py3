import numpy as np
import LL_calculators
from load_comparison_data import load_comparison_data
import matplotlib.pyplot as plt
import json
from parsers_malaria import get_site_data
import matplotlib.cm as cm

def analyze_clinical_incidence_by_age(analyzer, site, data) :

    raw_data_all = load_comparison_data(site, 'annual_clinical_incidence_by_age')
    age_bins = raw_data_all['age_bins']

    LL = [0]*len(data['Average Population by Age Bin'])
    for field in analyzer['fields_to_get'] :
        if field != 'Annual Clinical Incidence by Age Bin' :
            continue
        raw_data_field = fraction_to_number(raw_data_all['n_obs'], raw_data_all[field])
        for rownum, row in enumerate(data[field]) :
            n_sim, sim_data, empty_bins = accumulate_agebins_cohort(row, data['Average Population by Age Bin'][rownum],
                                                                    data['Age Bins'][rownum], age_bins)
            n_sim, sim_data = remove_empty_bins(n_sim, sim_data, empty_bins)
            n_raw, raw_data = remove_empty_bins(raw_data_all['n_obs'], raw_data_field, empty_bins)
            LL[rownum] += LL_calculators.gamma_poisson(n_raw, n_sim, raw_data, sim_data)
    return LL

def visualize_clinical_incidence_by_age(settings, iteration, analyzer, site, samples, top_LL_index) :

    plot_best_LL(settings, iteration, site, [samples[site + ' outpath'][i] for i in top_LL_index])
    plot_all_LL(settings, iteration, site, analyzer, samples['LL'])

def plot_all_LL(settings, iteration, site, analyzer, LL) :

    data = get_site_data(settings, {}, site, iteration)[analyzer['name']]
    raw_data = load_comparison_data(site, 'annual_clinical_incidence_by_age')
    age_bins = raw_data['age_bins']
    channels = ['Annual Clinical Incidence by Age Bin']
    numchannels = len(channels)
    LL_max = max(LL)
    LL_min = min(LL)
    if LL_min == LL_max : LL_min = LL_max-1

    fname = settings['curr_iteration_dir'] + site + '_incidence_all'

    fig = plt.figure(fname, figsize=(4,numchannels*3))
    plt.subplots_adjust(left=0.15, bottom=0.15, right=0.95)

    for i, channel in enumerate(channels) :
        ax = fig.add_subplot(numchannels, 1, i+1)

        for rownum, row in enumerate(data[channel]) :
            n_sim, sim_data, empty_bins = accumulate_agebins_cohort(row, data['Average Population by Age Bin'][rownum],
                                                                    data['Age Bins'][rownum], age_bins)
            plot_incidence(ax, data, age_bins, channel, plotstyle='-', mycolor=cm.Blues((LL[rownum]-LL_min)/(LL_max-LL_min)), 
                            alpha=0.5, linewidth=0.5, n=n_sim, d=sim_data, empty=empty_bins)
        plot_incidence(ax, raw_data, age_bins, channel, ref=True, mycolor='#F9A11D')
        if i == numchannels-1 :
            ax.set_xlabel('age in years')
        ax.set_ylabel(channel)

    plt.savefig(fname + '.pdf', format='PDF')
    plt.close(fig)

def plot_best_LL(settings, iteration, site, outpaths) :

    channels = ['Annual Clinical Incidence by Age Bin']
    raw_data = load_comparison_data(site, 'annual_clinical_incidence_by_age')
    agebins = raw_data['age_bins']
    numchannels = len(channels)

    if iteration == 0 :
        fname = settings['exp_dir'] + site + '_reference_incidence'
        fig = plt.figure(fname, figsize=(4,numchannels*3))
        plt.subplots_adjust(left=0.15, bottom=0.15, right=0.95)
        for i, channel in enumerate(channels) :
            ax = fig.add_subplot(numchannels, 1, i+1)
            plot_incidence(ax, raw_data, agebins, channel, ref=True, mycolor='#F9A11D')
            if i == numchannels-1 :
                ax.set_xlabel('age in years')
            ax.set_ylabel(channel)
        plt.savefig(fname + '.pdf', format='PDF')
        plt.close(fig)
    
    for j, outpath in enumerate(outpaths) :
        fname = settings['curr_iteration_dir'] + site + '_incidence_' + str(j)
        data = get_summary_report_data(outpath)
        fig = plt.figure(fname, figsize=(4,numchannels*3))
        plt.subplots_adjust(left=0.15, bottom=0.15, right=0.95)
        for i, channel in enumerate(channels) :
            ax = fig.add_subplot(numchannels, 1, i+1)
            plot_incidence(ax, data, agebins, channel, mycolor='#C01E6C')
            if i == numchannels-1 :
                ax.set_xlabel('age in years')
            ax.set_ylabel(channel)
        plt.savefig(fname + '.pdf', format='PDF')
        plt.close(fig)

    return

def plot_incidence(ax, data, agebins, channel, ref=False, plotstyle='-o', mycolor='C01E6C', alpha=1, linewidth=1, n=[], d=[], empty=[]) :

    if ref :
        theseagebins = agebins
        d = data[channel]
    else :
        if n == [] and d == [] :
            pop = data['Average Population by Age Bin']
            n, d, empty = accumulate_agebins_cohort(data[channel], pop, data['Age Bins'], agebins)
        n, d = remove_empty_bins(n, d, empty)
        theseagebins = [agebins[x] for x in range(len(agebins)) if x not in empty]
        d = [d[x]/n[x] for x in range(len(d))]

    ax.plot(theseagebins, d, plotstyle, color=mycolor, alpha=alpha, linewidth=linewidth)

def get_summary_report_data(outpath) :

    simfile = 'MalariaSummaryReport_Annual_Report.json'
    with open(outpath + '/output/' + simfile) as fin :
        return json.loads(fin.read()) 

def remove_empty_bins(n_obs, data, empty_bins) :

    n = [n_obs[i] for i in range(len(n_obs)) if i not in empty_bins]
    d = [data[i] for i in range(len(data)) if i not in empty_bins]

    return n, d

def fraction_to_number(n, f) :

    return [f[i]*n[i] for i in range(len(n))]

def accumulate_agebins_cohort(simdata, average_pop, sim_agebins, raw_agebins) :

    glommed_data = [0]*len(raw_agebins)
    simageindex = [-1]*len(sim_agebins)
    yearageindex = [-1]*len(simdata)
    num_in_bin = [0]*len(raw_agebins)

    for i in range(len(simageindex)) :
        for j, age in enumerate(raw_agebins) :
            if sim_agebins[i] < age :
                simageindex[i] = j
                break
    for i in range(len(yearageindex)) :
        for j, age in enumerate(raw_agebins) :
            if i < age :
                yearageindex[i] = j
                break

    empty_bins = [i for i in range(len(raw_agebins)) if i not in simageindex]

    for i in range(len(yearageindex)) :
        if yearageindex[i] < 0 :
            continue
        for j in range(len(simageindex)) :
            if simageindex[j] < 0 :
                continue
            glommed_data[simageindex[j]] += simdata[i][j]*average_pop[i][j]
            num_in_bin[simageindex[j]] += average_pop[i][j]

    return num_in_bin, glommed_data, empty_bins


