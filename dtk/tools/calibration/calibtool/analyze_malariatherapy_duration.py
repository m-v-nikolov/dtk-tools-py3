import numpy as np
import json
import LL_calculators
from load_comparison_data import load_comparison_data
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator
from parsers_malaria import get_site_data
import matplotlib.cm as cm

def analyze_malariatherapy_duration(analyzer, site, data) :

    raw_data = load_comparison_data(site, 'density_timecourse')
    numsamples = len(data)
    
    LL = [0]*numsamples
    for rownum in range(numsamples) :
        LL[rownum] += compare_durations(raw_data, data[rownum])

    return LL

def visualize_malariatherapy_duration(settings, iteration, analyzer, site, samples, top_LL_index) :

    plot_best_LL(settings, iteration, site, [samples[site + ' outpath'][i] for i in top_LL_index])
    plot_all_LL(settings, iteration, site, analyzer, samples['LL'])

def plot_all_LL(settings, iteration, site, analyzer, LL) :

    data = get_site_data(settings, {}, site, iteration)[analyzer['name']]
    raw_data = load_comparison_data(site, 'density_timecourse')
    numsamples = len(data)
    duration_bins = raw_data['infection_duration_bins']
    dur_channels = ['parasitemia_durations', 'gametocytemia_durations']
    numchannels = len(dur_channels)
    LL_max = max(LL)
    LL_min = min(LL)
    if LL_min == LL_max : LL_min = LL_max-1
        
    fname = settings['curr_iteration_dir'] + site + '_duration_all'

    fig = plt.figure(fname, figsize=(6,numchannels*3))    
    plt.subplots_adjust(hspace=0.5)

    for i, channel in enumerate(dur_channels) :
        ax = fig.add_subplot(numchannels, 1, i+1)
        for rownum in range(numsamples) :
            plot_duration(ax, data[rownum], channel, duration_bins, plottype='line', plotstyle='-', mycolor=cm.Blues((LL[rownum]-LL_min)/(LL_max-LL_min)))
        plot_duration(ax, raw_data, channel, duration_bins, ref=True, plottype='line', plotstyle='-o', mycolor='#F9A11D', alpha=1)

    fig.savefig(fname + '.pdf', format='PDF')
    plt.close(fig)

def plot_best_LL(settings, iteration, site, outpaths) :

    raw_data = load_comparison_data(site, 'density_timecourse')
    dur_channels = ['parasitemia_durations', 'gametocytemia_durations']
    dur_bins = raw_data['infection_duration_bins']
    numchannels = len(dur_channels)

    if iteration == 0 :
        fname = settings['exp_dir'] + site + '_reference_duration'

        fig = plt.figure(fname, figsize=(6,numchannels*3))    
        plt.subplots_adjust(hspace=0.5)

        for i, channel in enumerate(dur_channels) :
            ax = fig.add_subplot(numchannels, 1, i+1)
            plot_duration(ax, raw_data, channel, dur_bins, ref=True, plottype='bar', mycolor='#F9A11D')

        fig.savefig(fname + '.pdf', format='PDF')
        plt.close(fig)

    for j, outpath in enumerate(outpaths) :
        data = get_survey_report_data(outpath, ['true_asexual_parasites', 'true_gametocytes'])
        plot_individual_traces(settings['curr_iteration_dir'] + site + '_individuals_' + str(j), data)

        fname = settings['curr_iteration_dir'] + site + '_duration_' + str(j)

        fig = plt.figure(fname, figsize=(6,numchannels*3))    
        plt.subplots_adjust(hspace=0.5)

        for i, channel in enumerate(dur_channels) :
            ax = fig.add_subplot(numchannels, 1, i+1)
            plot_duration(ax, data, channel, dur_bins, plottype='bar', mycolor='#C01E6C')

        fig.savefig(fname + '.pdf', format='PDF')
        plt.close(fig)

def plot_duration(ax, data, channel, bins, ref=False, plottype='bar', plotstyle='-', mycolor='#C01E6C', alpha=0.5) :

    if ref :
        d = data
    else :
        d = { 'parasitemia_durations' : get_durations(data, bins, 'true_asexual_parasites', detection=10),
              'gametocytemia_durations' : get_durations(data, bins, 'true_gametocytes', detection=10) }

    if plottype == 'bar' :
        ax.bar([x for x in range(len(bins))], [100.*x/sum(d[channel]) for x in d[channel]], 
                color=mycolor, alpha=alpha)
    else :
        ax.plot([x for x in range(len(bins))], [100.*x/sum(d[channel]) for x in d[channel]], 
                plotstyle, color=mycolor, alpha=alpha)

    ax.xaxis.set_major_locator(FixedLocator(range(len(bins))))
    ax.set_xticklabels(['<' + str(x) for x in bins])
    ax.set_xlabel(channel + ' in days')
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

def compare_durations(raw_data, sim_data) :

    duration_bins = raw_data['infection_duration_bins']
    sim_a = get_durations(sim_data, duration_bins, 'true_asexual_parasites', detection=10)
    sim_g = get_durations(sim_data, duration_bins, 'true_gametocytes', detection=10)

    LL = 0
    LL += LL_calculators.dirichlet_single(raw_data['parasitemia_durations'], sim_a)
    LL += LL_calculators.dirichlet_single(raw_data['gametocytemia_durations'], sim_g)    

    return LL

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
