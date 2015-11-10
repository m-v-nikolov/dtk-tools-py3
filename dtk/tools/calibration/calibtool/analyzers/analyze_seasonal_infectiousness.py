# Template script for analyzing and visualizing simulation output from calibtool
#
# Replace all instances of TEMPLATE with new analyzer name.
# Replace all instances of DATATYPE with data descriptor
#
#

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

def analyze_seasonal_infectiousness(settings, analyzer, site, data, samples) :

    LL_fn = getattr(LL_calculators, analyzer['LL_fn'])
    raw_data = get_reference_data(site, 'infectiousness_by_age_and_season')
    inf_bins = raw_data['fraction_infected_bins']
    age_bins = raw_data['age_bins']
    gam_bins = get_reference_data(site, 'density_and_infectiousness_by_age_and_season')['parasitemia_bins']
    
    seasons = analyzer['seasons']
    numsamples = len(samples.index)
    paramnames = list(samples.columns.values)

    LL = [0]*len(samples.index)
    scale_factor=1
    min_inf=1
    ad_age=1
    seas_m=1
    if 'Acquire_Modifier' in paramnames :
        scale_factor = samples['Acquire_Modifier'].values
    if 'Age_Dependent_Decrease_In_Infectivity_Min_Infectivity' in paramnames :
        min_inf = samples['Age_Dependent_Decrease_In_Infectivity_Min_Infectivity'].values
    if 'Age_Dependent_Decrease_In_Infectivity_Adult_Age' in paramnames :
        ad_age = samples['Age_Dependent_Decrease_In_Infectivity_Adult_Age'].values
    if 'Seasonal_Multiplier' in paramnames :
        seas_m = samples['Seasonal_Multiplier'].values

    record_data_by_sample = { 'infectiousness_by_age_and_season' : {},
                              'density_and_infectiousness_by_age_and_season' : {}  }
    for season in seasons :
        record_data_by_sample['infectiousness_by_age_and_season'][season] = []
        record_data_by_sample['density_and_infectiousness_by_age_and_season'][season] = []
    for rownum in range(len(LL)) :

        for i, season in enumerate(seasons) :
            date = int(365/12.*seasons[season])

            sim_data = []
            sim_gam = []
            for y in range(settings['sim_runs_per_param_set']) :
                sim_inf = get_infectiousness_at_date(data[y][rownum], inf_bins, age_bins, date, scale_factor, min_inf, ad_age, seas_m**i)
                sim_gam_inf = get_gametocytemia_and_infectiousness_at_date(data[y][rownum], inf_bins, gam_bins, age_bins, date, scale_factor, min_inf, ad_age, seas_m**i)
                sim_data.append(sim_inf)
                sim_gam.append(sim_gam_inf)
            mean_sim_data = [[np.mean([sim_data[y][x][z] for y in range(settings['sim_runs_per_param_set'])]) for z in range(len(inf_bins))] for x in range(len(age_bins))]

            LL[rownum] += LL_fn(np.array(raw_data[season]['infectiousness']), np.array(mean_sim_data))
            record_data_by_sample['infectiousness_by_age_and_season'][season].append(mean_sim_data)
            record_data_by_sample['density_and_infectiousness_by_age_and_season'][season].append([[[np.mean([sim_gam[y][a][x][z] for y in range(settings['sim_runs_per_param_set'])]) for z in range(len(inf_bins))] for x in range(len(gam_bins))] for a in range(len(age_bins))])

    with open(settings['curr_iteration_dir'] + site + '_' + analyzer['name'] + '.json', 'w') as fout :
        json.dump(record_data_by_sample, fout)
    return LL

def visualize_seasonal_infectiousness(settings, iteration, analyzer, site, samples, top_LL_index) :

    plot_best_LL(settings, iteration, site, analyzer, samples, top_LL_index)
    plot_all_LL(settings, iteration, site, analyzer, samples)

def plot_best_LL(settings, iteration, site, analyzer, samples, top_LL_index) :
        
    raw_data = { 'inf_data' : get_reference_data(site, 'infectiousness_by_age_and_season'),
                'gam_inf_data' : get_reference_data(site, 'density_and_infectiousness_by_age_and_season') }

    age_bins = raw_data['inf_data']['age_bins']
    inf_bins = raw_data['inf_data']['fraction_infected_bins']
    gam_bins = raw_data['gam_inf_data']['parasitemia_bins']
    gam_bins[0] = 0.005
    seasons = analyzer['seasons']

    for j, LL_index in enumerate(top_LL_index) :
        iter = samples['iteration'].values[LL_index]
        prevsamples = len(samples[samples['iteration'] < iter].index)
        rownum = LL_index-prevsamples
        with open(settings['exp_dir'] + 'iter' + str(iter) + '/' + site + '_' + analyzer['name'] + '.json') as fin :
            data = json.loads(fin.read())['density_and_infectiousness_by_age_and_season']

        fname = settings['plot_dir'] + site + '_inf_vs_gam_density_LLrank' + str(j)
        sns.set_style('white')
        fig = plt.figure(fname, figsize=(len(seasons)*4,len(age_bins)*3))
        plt.subplots_adjust(left=0.15, bottom=0.15, right=0.95)
        for a, age in enumerate(age_bins) :
            for s, season in enumerate(seasons) :
                ax = fig.add_subplot(len(age_bins), len(seasons), a*len(seasons) + s + 1)    
                plot_bubbles(ax, np.array(data[season][rownum][a]), gam_bins, inf_bins, color='#CB5FA4')
                plot_bubbles(ax, np.array(raw_data['gam_inf_data'][season]['Gametocytemia and Infectiousness'][a]), gam_bins, inf_bins, color='#8DC63F')

                if s == 0 :
                    ax.set_ylabel('pct mos inf')
                else :
                    ax.set_yticklabels([])
                if a == len(age_bins)-1 :
                    ax.set_xlabel('gametocyte_density')
                else :
                    ax.set_xticklabels([])
                ax.set_title(season + ' age <' + str(age))
                ax.set_xlim(10**-3, 10**6)
                ax.set_ylim(0, 100)

        plt.savefig(fname + '.pdf', format='PDF')
        plt.close(fig)


def plot_all_LL(settings, iteration, site, analyzer, samples) :

    raw_data = get_reference_data(site, 'infectiousness_by_age_and_season')
    inf_bins = raw_data['fraction_infected_bins']
    age_bins = raw_data['age_bins']
    seasons = analyzer['seasons']

    LL = samples['LL'].values
    LL_max = max(LL)
    LL_min = min(LL)
    if LL_min == LL_max : LL_min = LL_max-1

    fname = settings['plot_dir'] + site + '_infectiousness_by_age_all'
    sns.set_style('white')
    fig = plt.figure(fname, figsize=(len(seasons)*4,len(age_bins)*3))
    plt.subplots_adjust(left=0.15, bottom=0.15, right=0.95)
    for a, age in enumerate(age_bins) :
        for s, season in enumerate(seasons) :
            ax = fig.add_subplot(len(age_bins), len(seasons), a*len(seasons) + s + 1)    

            grouped = samples.groupby('iteration')
            prevsamples = 0
            for i, (iter, df_iter) in enumerate(grouped) :
                with open(settings['exp_dir'] + 'iter' + str(iter) + '/' + site + '_' + analyzer['name'] + '.json') as fin :
                    data = json.loads(fin.read())['infectiousness_by_age_and_season']
                for rownum, sim_data in enumerate(data[season]) :
                    plot(ax, inf_bins, sim_data[a], style='-', color=cm.Blues((LL[rownum + prevsamples]-LL_min)/(LL_max-LL_min)), alpha=0.5, linewidth=0.5)
                prevsamples += len(df_iter.index)

            plot(ax, inf_bins, raw_data[season]['infectiousness'][a], style='-o', color='#8DC63F', alpha=1, linewidth=1)
            if a == len(age_bins)-1 :
                ax.set_xlabel('pct mos inf')
            else :
                ax.set_xticklabels([])
            if s == 0 :
                ax.set_ylabel('fraction of age group')
            else :
                ax.set_yticklabels([])
            ax.set_title(season + ' age <' + str(age))
            ax.set_xlim(0, 100)
            ax.set_ylim(0, 1)

    plt.savefig(fname + '.pdf', format='PDF')
    plt.close(fig)

def plot(ax, bins, data, style='-o', color='#CB5FA4', alpha=0.5, linewidth=0.5) :

    ax.plot(bins, [1.*x/sum(data) for x in data], style, color=color, alpha=alpha, linewidth=linewidth) 

def plot_bubbles(ax, data, density_bins, inf_bins, color='#CB5FA4') :

    ndata = 1.*data/np.sum(data)
    for j in range(len(inf_bins)) :
        for k in range(len(density_bins)-1) :
            ax.semilogx(density_bins[k], inf_bins[j], 'o', markersize=50*math.sqrt(ndata[k, j]), 
                        markerfacecolor=color, alpha=0.5, linewidth=0)
    """
    ax.set_ylim(10**-1, 10**7)
    ax.set_xlim(-1, 3)
    ax.xaxis.set_major_locator(FixedLocator(range(len(age_bins))))
    ax.set_xticklabels(['<' + str(age) for age in age_bins])
    ax.yaxis.set_major_locator(FixedLocator(density_bins))     
    """
    return

def get_infectiousness_at_date(data, inf_bins, agebins, date, scale_factor=1, min_inf=1, ad_age=100, seas_m=1) :

    agebins = [0] + agebins
    fracinf = []
    for i in range(len(agebins)-1) :
        d = get_data_by_age_field_and_day(data, 'infectiousness', date, agebins[i]*365, agebins[i+1]*365, scale_factor, min_inf, ad_age, seas_m)
        y = [0]*len(inf_bins)
        for item in d :
            for j, val in enumerate(inf_bins) :
                if item <= val :
                    y[j] += 1
                    break
        fracinf.append(y)

    return np.array(fracinf)

def get_gametocytemia_and_infectiousness_at_date(data, inf_bins, gam_bins, agebins, date, scale_factor=1, min_inf=1, ad_age=100, seas_m=1) :

    binned_data = np.zeros((len(agebins), len(gam_bins), len(inf_bins)))
    totalpop = [0]*len(agebins)

    theseagebins = [0] + agebins
    for i in range(len(theseagebins)-1) :
        inf = get_data_by_age_field_and_day(data, 'infectiousness', date, theseagebins[i]*365, theseagebins[i+1]*365, scale_factor, min_inf, ad_age, seas_m)
        gam = get_data_by_age_field_and_day(data, 'true_gametocytes', date, theseagebins[i]*365, theseagebins[i+1]*365)

        for j in range(len(inf)) :
            gindex, iindex = 0, 0
            for tt, val in enumerate(gam_bins) :
                if gam[j] <= val :
                    gindex = tt
                    break
            for tt, val in enumerate(inf_bins) :
                if inf[j] <= val :
                    iindex = tt
                    break
            binned_data[i, gindex, iindex] += 1
            totalpop[i] += 1

    return binned_data

def get_data_by_age_field_and_day(data, field, date, agemin_in_days=0, agemax_in_days=200, scale_factor=1, min_inf=1, ad_age=100, seas_m=1) :

    d = []
    for patient in data :
        age = patient['initial_age'] + date
        if age >= agemin_in_days and age <= agemax_in_days :
            try :
                if field == 'infected_mosquito_fraction' or field == 'infectiousness' :
                    #t = patient[field][date]*get_age_biting_modifier(age/365.)*scale_factor*(1+age/365.*(min_inf-1)/ad_age)*seas_m
                    t = patient[field][date]*scale_factor*(1+age/365.*(min_inf-1)/ad_age)*seas_m
                    d.append(t if t >= 1 else 0)
                else :
                    d.append(patient[field][date])
            except IndexError :
                pass

    return d

def get_age_biting_modifier(age) :

    newborn_risk = 0.07
    two_yo_risk = 0.23

    if age < 2 :
        return newborn_risk + age*(two_yo_risk - newborn_risk)/2.
    if age < 20 :
        return two_yo_risk + (age - 2)*(1 - two_yo_risk)/(20-2.)
    else :
        return 1.