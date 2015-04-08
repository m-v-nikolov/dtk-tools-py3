import numpy as np
import json
import LL_calculators
from load_comparison_data import load_comparison_data
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator
from math import sqrt
from parsers_malaria import get_site_data
import matplotlib.cm as cm

def analyze_seasonal_monthly_density(analyzer, site, data) :

    raw_data = load_comparison_data(site, 'density_by_age_and_season')
    agebins = raw_data['age_bins']

    LL = [0]*len(data['Average Population by Age Bin'])
    for field in analyzer['fields_to_get'] :
        if field == 'Average Population by Age Bin' :
            continue
        for rownum, row in enumerate(data[field]) :
            for season in analyzer['seasons'] :
                glom_every = range(analyzer['seasons'][season], len(row), 12)
                sim_data = accumulate_agebins_cohort_2D(row, data['Average Population by Age Bin'][rownum], 
                                                        agebins, glom_every, 12)
                LL[rownum] += LL_calculators.dirichlet_multinomial(raw_data[season][field], sim_data)
    return LL

def visualize_seasonal_monthly_density(settings, iteration, analyzer, site, samples, top_LL_index) :

    plot_best_LL(settings, iteration, site, analyzer, [samples[site + ' outpath'][i] for i in top_LL_index])
    plot_all_LL(settings, iteration, site, analyzer, samples['LL'])

def plot_all_LL(settings, iteration, site, analyzer, LL) :

    data = get_site_data(settings, {}, site, iteration)[analyzer['name']]
    raw_data = load_comparison_data(site, 'density_by_age_and_season')
    agebins = raw_data['age_bins']
    dtypes = ['parasitemia', 'gametocytemia']
    channels = ['PfPR by ' + x.title() + ' and Age Bin' for x in dtypes]
    seasons = ['start_wet', 'peak_wet', 'end_wet']
    bins = raw_data['parasitemia_bins']
    theseagebins = [0] + agebins
    LL_max = max(LL)
    LL_min = min(LL)
    if LL_min == LL_max : LL_min = LL_max-1

    for cindex, channel in enumerate(channels) :
        fname = settings['curr_iteration_dir'] + site + '_' + dtypes[cindex] + '_density_all'
        fig = plt.figure(fname, figsize=(len(seasons)*4, len(agebins)*3))
        plt.subplots_adjust(left=0.1, right=0.95, bottom=0.1, top=0.95, hspace=0.25)
        for rownum, row in enumerate(data[channel]) :
            for sindex, season in enumerate(analyzer['seasons']) :
                glom_every = range(analyzer['seasons'][season], len(row), 12)
                sim_data = accumulate_agebins_cohort_2D(row, data['Average Population by Age Bin'][rownum], 
                                                        agebins, glom_every, 12)
                for ageindex in range(len(agebins)) :
                    ax = fig.add_subplot(len(seasons), len(agebins), ageindex*(len(seasons))+sindex+1)
                    plot_lines(ax, [float(x)/sum(sim_data[ageindex]) for x in sim_data[ageindex]], bins, plotstyle='-', linewidth=0.5, mycolor=cm.Blues((LL[rownum]-LL_min)/(LL_max-LL_min)), 
                               alpha=0.5)
        
        for sindex, season in enumerate(analyzer['seasons']) :
            for ageindex in range(len(agebins)) :
                ax = fig.add_subplot(len(seasons), len(agebins), ageindex*(len(seasons))+sindex+1)
                plot_lines(ax, [float(x)/sum(raw_data[season][channel][ageindex,:]) for x in raw_data[season][channel][ageindex,:]], bins, mycolor='#F9A11D', alpha=1)
                ax.set_title('age ' + str(theseagebins[ageindex]) + ' to ' + str(theseagebins[ageindex+1]) + ' ' + season)
                ax.set_xlim(10**-1, 10**7)
                ax.set_xscale('log')
                if ageindex == len(agebins)-1 :
                    ax.set_xlabel(dtypes[cindex] + ' per uL')
                if sindex == 0 :
                    ax.set_ylabel('frac population')
        plt.savefig(fname + '.pdf', format='PDF')
        plt.close(fig)

def plot_best_LL(settings, iteration, site, analyzer, outpaths) :

    channels = ['PfPR by Parasitemia and Age Bin', 'PfPR by Gametocytemia and Age Bin']
    raw_data = load_comparison_data(site, 'density_by_age_and_season')
    agebins = raw_data['age_bins']
    seasons = ['start_wet', 'peak_wet', 'end_wet']

    if iteration == 0 :
        plot_bubbles(settings['exp_dir'] + site + '_reference_density', raw_data, agebins, channels, 
                     seasons, analyzer, ref=True)
    
    for i, outpath in enumerate(outpaths) :
        data = get_summary_report_data(outpath)
        plot_bubbles(settings['curr_iteration_dir'] + site + '_density_' + str(i), data, agebins, channels, 
                     seasons, analyzer)

def plot_lines(ax, data, bins, plotstyle='-o', linewidth=1, mycolor='#C01E6C', alpha=1) :

    ax.plot(bins, data, plotstyle, linewidth=linewidth, color=mycolor, alpha=alpha)

def plot_bubbles(fname, data, agebins, channels, seasons, analyzer, ref=False) :

    numchannels = len(channels)
    if ref :
        bins = data['parasitemia_bins']
        bins[0] = 0.5
        mycolor = '#F9A11D'
    else :
        bins = [0.5] + data['Parasitemia Bins']
        if bins[-1] > 1e8 :
            bins[-1] = 500000
        mycolor = '#C01E6C'
        pop = data['Average Population by Age Bin']

    fig = plt.figure(fname, figsize=(len(seasons)*4,numchannels*3))    

    for i, channel in enumerate(channels) :
        for mindex, m in enumerate(seasons) :
            if ref :
                d = data[m][channel]
            else :
                d = data[channel]
                glom_every = range(analyzer['seasons'][m], len(d), 12)
                d = accumulate_agebins_cohort_2D(d, pop, agebins, glom_every, 12)

            ax = fig.add_subplot(numchannels, len(seasons), i*(len(seasons))+mindex+1)

            for j in range(len(agebins)) :
                for k in range(len(bins)-1) :
                    ax.semilogy(j, bins[k], 'o', markersize=50*sqrt(1.*d[j, k]/(sum(d[j, :]))), 
                                markerfacecolor=mycolor, alpha=0.5)

            ax.set_ylim(10**-1, 10**7)
            ax.set_xlim(-1, 3)
            ax.xaxis.set_major_locator(FixedLocator(range(len(agebins))))
            ax.set_xticklabels(['<' + str(age) for age in agebins])
            ax.yaxis.set_major_locator(FixedLocator(bins))            
            
            if mindex == 0 :
                ax.set_ylabel(channel.split()[2] + ' density')
                ax.set_yticklabels(['none'] + ['<' + str(x) for x in bins[1:]])
            if i == numchannels-1 :
                ax.set_xlabel('age in years')
            if i == 0 :
                ax.set_title('month = ' + str(m))

    plt.savefig(fname + '.pdf', format='PDF')
    plt.close(fig)

def get_summary_report_data(outpath) :

    simfile = 'MalariaSummaryReport_Monthly_Report.json'
    with open(outpath + '/output/' + simfile) as fin :
        return json.loads(fin.read())    

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
