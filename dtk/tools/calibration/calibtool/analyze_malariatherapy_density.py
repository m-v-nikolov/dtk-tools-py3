import numpy as np
import json
import LL_calculators
from load_comparison_data import load_comparison_data
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator
from parsers_malaria import get_site_data
import matplotlib.cm as cm

def analyze_malariatherapy_density(analyzer, site, data) :

    raw_data = load_comparison_data(site, 'density_timecourse')
    numsamples = len(data)
    
    LL = [0]*numsamples
    for rownum in range(numsamples) :
        LL[rownum] += compare_peak_densities(raw_data, data[rownum])

    return LL

def visualize_malariatherapy_density(settings, iteration, analyzer, site, samples, top_LL_index) :

    plot_best_LL(settings, iteration, site, [samples[site + ' outpath'][i] for i in top_LL_index])
    plot_all_LL(settings, iteration, site, analyzer, samples['LL'])

def plot_all_LL(settings, iteration, site, analyzer, LL) :

    data = get_site_data(settings, {}, site, iteration)[analyzer['name']]
    raw_data = load_comparison_data(site, 'density_timecourse')
    numsamples = len(data)
    density_bins = raw_data['parasitemia_bins']
    peak_channels = ['peak_parasitemias', 'peak_gametocytemias']
    numchannels = len(peak_channels)
    LL_max = max(LL)
    LL_min = min(LL)
    if LL_min == LL_max : LL_min = LL_max-1
        
    fname = settings['curr_iteration_dir'] + site + '_peak_density_all'

    fig = plt.figure(fname, figsize=(6,numchannels*3))    
    plt.subplots_adjust(hspace=0.5)

    for i, channel in enumerate(peak_channels) :
        ax = fig.add_subplot(numchannels, 1, i+1)
        for rownum in range(numsamples) :
            plot_peak_density(ax, data[rownum], channel, density_bins, plottype='line', plotstyle='-', mycolor=cm.Blues((LL[rownum]-LL_min)/(LL_max-LL_min)))
        plot_peak_density(ax, raw_data, channel, density_bins, ref=True, plottype='line', plotstyle='-o', mycolor='#F9A11D', alpha=1)

    fig.savefig(fname + '.pdf', format='PDF')
    plt.close(fig)

def plot_best_LL(settings, iteration, site, outpaths) :

    raw_data = load_comparison_data(site, 'density_timecourse')
    peak_channels = ['peak_parasitemias', 'peak_gametocytemias']
    peak_bins = raw_data['parasitemia_bins']
    numchannels = len(peak_channels)

    if iteration == 0 :
        fname = settings['exp_dir'] + site + '_reference_peak_density'

        fig = plt.figure(fname, figsize=(6,numchannels*3))    
        plt.subplots_adjust(hspace=0.5)

        for i, channel in enumerate(peak_channels) :
            ax = fig.add_subplot(numchannels, 1, i+1)
            plot_peak_density(ax, raw_data, channel, peak_bins, ref=True, plottype='bar', mycolor='#F9A11D')

        fig.savefig(fname + '.pdf', format='PDF')
        plt.close(fig)

    for j, outpath in enumerate(outpaths) :
        data = get_survey_report_data(outpath, ['true_asexual_parasites', 'true_gametocytes'])
        plot_individual_traces(settings['curr_iteration_dir'] + site + '_individuals_' + str(j), data)

        fname = settings['curr_iteration_dir'] + site + '_peak_density_' + str(j)

        fig = plt.figure(fname, figsize=(6,numchannels*3))    
        plt.subplots_adjust(hspace=0.5)

        for i, channel in enumerate(peak_channels) :
            ax = fig.add_subplot(numchannels, 1, i+1)
            plot_peak_density(ax, data, channel, peak_bins, plottype='bar', mycolor='#C01E6C')

        fig.savefig(fname + '.pdf', format='PDF')
        plt.close(fig)

def plot_peak_density(ax, data, channel, bins, ref=False, plottype='bar', plotstyle='-', mycolor='#C01E6C', alpha=0.5) :

    if ref :
        d = data
    else :
        d = { 'peak_parasitemias' : get_peak_densities(data, bins, 'true_asexual_parasites'),
              'peak_gametocytemias' : get_peak_densities(data, bins, 'true_gametocytes') }

    if plottype == 'bar' :
        ax.bar([x for x in range(len(bins))], [100.*x/sum(d[channel]) for x in d[channel]], 
                color=mycolor, alpha=0.5)
    else :
        ax.plot([x for x in range(len(bins))], [100.*x/sum(d[channel]) for x in d[channel]], 
                plotstyle, color=mycolor, alpha=0.5)

    ax.xaxis.set_major_locator(FixedLocator(range(len(bins))))
    ax.set_xticklabels(['<' + str(x) for x in bins])
    ax.set_xlabel(channel + ' in uL')
    ax.set_ylabel('percent of patients')
    ax.set_xlim(-0.5, len(bins)+0.5)

def plot_individual_traces(fname, data) :

    num_inds = 8
    num_days = 250
    a_color = '#35478C'
    g_color = '#45BF55'

    fig = plt.figure(fname, figsize=(10, 8))    
    ax1 = fig.add_subplot(111)

    for i in range(num_inds) :
        ax = fig.add_subplot(4,2,i+1)
        patient = data[i]

        ax.plot(range(num_days), patient['true_asexual_parasites'][:num_days], '-', color=a_color)
        ax.plot(range(num_days), patient['true_gametocytes'][:num_days], '-', color=g_color)

        ax.set_yscale('log')
        ax.set_xlim(0, num_days)
        ax.set_ylim(10**-7, 10**7)
        ax.yaxis.set_major_locator(FixedLocator([10**(2*x) for x in range(-3, 4)]))

    ax1.spines['top'].set_color('none')
    ax1.spines['bottom'].set_color('none')
    ax1.spines['left'].set_color('none')
    ax1.spines['right'].set_color('none')
    ax1.tick_params(labelcolor='w', top='off', bottom='off', left='off', right='off')

    ax1.set_xlabel('days')
    ax1.set_ylabel('density in uL')

    plt.savefig(fname + '.pdf', format='PDF')

    return

def get_survey_report_data(simpath, channels, start_day=1) :

    simfile = 'MalariaSurveyJSONAnalyzer_Day_' + str(start_day) + '_' + str(0) + '.json'
    with open(simpath + '/output/' + simfile) as fin :
        all_data = json.loads(fin.read())
    patients = []
    for patient in all_data['patient_array'] :
        d = {}
        for channel in channels :
            d[channel] = patient[channel][0]
        patients.append(d)
    return patients

def compare_peak_densities(raw_data, sim_data) :

    density_bins = raw_data['parasitemia_bins']
    sim_a = get_peak_densities(sim_data, density_bins, 'true_asexual_parasites')
    sim_g = get_peak_densities(sim_data, density_bins, 'true_gametocytes')

    LL = 0
    LL += LL_calculators.dirichlet_single(raw_data['peak_parasitemias'], sim_a)
    LL += LL_calculators.dirichlet_single(raw_data['peak_gametocytemias'], sim_g)

    return LL

def get_peak_densities(data, bins, partype) :

    binned_peaks = [0.]*len(bins)

    for patient in data :
        max_density = max(patient[partype])
        for i, this_bin in enumerate(bins) :
            if max_density < this_bin :
                binned_peaks[i] += 1
                break

    return binned_peaks

