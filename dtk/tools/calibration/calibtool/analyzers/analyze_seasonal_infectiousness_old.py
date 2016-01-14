import os

import numpy as np
import json
import LL_calculators
from load_comparison_data import load_comparison_data
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator
from math import sqrt
from parsers_malaria import get_site_data
import matplotlib.cm as cm
import pandas as pd

def analyze_seasonal_infectiousness(settings, analyzer, site, data, samples) :

    raw_data = load_comparison_data(settings, site, 'infectiousness_by_age_and_season')
    agebins = raw_data['age_bins']
    numsamples = len(data)
    
    LL = [0]*numsamples
    scale_factor = [1]*numsamples
    ad_age = [100]*numsamples
    min_inf = [1]*numsamples
    seas_m = [1]*numsamples
    paramnames = list(samples.columns.values)
    if 'Acquire_Modifier' in paramnames :
        scale_factor = samples['Acquire_Modifier'].values
    if 'Age_Dependent_Decrease_In_Infectivity_Min_Infectivity' in paramnames :
        min_inf = samples['Age_Dependent_Decrease_In_Infectivity_Min_Infectivity'].values
    if 'Age_Dependent_Decrease_In_Infectivity_Adult_Age' in paramnames :
        ad_age = samples['Age_Dependent_Decrease_In_Infectivity_Adult_Age'].values
    if 'Seasonal_Multiplier' in paramnames :
        seas_m = samples['Seasonal_Multiplier'].values
    for rownum in range(numsamples) :
        LL[rownum] += compare_infectiousness(raw_data, data[rownum], agebins, analyzer['seasons'], analyzer['start_day'], scale_factor[rownum], min_inf[rownum], ad_age[rownum], seas_m[rownum])

    return LL

def visualize_seasonal_infectiousness(settings, iteration, analyzer, site, samples, top_LL_index) :

    plot_best_LL(settings, iteration, analyzer, site, samples, top_LL_index)
    plot_all_LL(settings, iteration, analyzer, site, samples)

def plot_all_LL(settings, iteration, analyzer, site, samples) :

    data = get_site_data(settings, {}, site, iteration)[analyzer['name']]
    raw_data = load_comparison_data(settings, site, 'infectiousness_by_age_and_season')
    agebins = raw_data['age_bins']
    inf_bins = raw_data['fraction_infected_bins']
    seasons = ['start_wet', 'peak_wet', 'end_wet']
    numsamples = len(data)
    theseagebins = [0] + agebins
    LL_max = max(samples['LL'].values)
    LL_min = min(samples['LL'].values)
    if LL_min == LL_max : LL_min = LL_max-1
    
    scale_factor = [1]*numsamples
    ad_age = [100]*numsamples
    min_inf = [1]*numsamples
    seas_m = [1]*numsamples
    paramnames = list(samples.columns.values)
    if 'Acquire_Modifier' in paramnames :
        scale_factor = samples['Acquire_Modifier'].values
    if 'Age_Dependent_Decrease_In_Infectivity_Min_Infectivity' in paramnames :
        min_inf = samples['Age_Dependent_Decrease_In_Infectivity_Min_Infectivity'].values
    if 'Age_Dependent_Decrease_In_Infectivity_Adult_Age' in paramnames :
        ad_age = samples['Age_Dependent_Decrease_In_Infectivity_Adult_Age'].values
    if 'Seasonal_Multiplier' in paramnames :
        seas_m = samples['Seasonal_Multiplier'].values

    fname = os.path.join(settings['plot_dir'],site + '_infectiousness_all')
    fig = plt.figure(fname, figsize=(len(seasons)*4, len(agebins)*3))
    plt.subplots_adjust(left=0.1, right=0.95, bottom=0.1, top=0.95, hspace=0.25)

    for rownum in range(numsamples) :
        d, totalpop = {}, {}
        for sindex, season in enumerate(seasons) :
            date = int(365/12.*analyzer['seasons'][season])
            d[season] = get_infectiousness_at_date(data[rownum], inf_bins, agebins, date, scale_factor[rownum], min_inf[rownum], ad_age[rownum], (seas_m[rownum])**sindex)
        for ageindex in range(len(agebins)) :
            for sindex, season in enumerate(seasons) :            
                ax = fig.add_subplot(len(agebins), len(seasons), ageindex*(len(seasons))+sindex+1)
                plot_lines(ax, [float(x)/sum(d[season][ageindex,:]) for x in d[season][ageindex,:]], inf_bins, plotstyle='-', linewidth=0.5, mycolor=cm.Blues((samples['LL'][rownum]-LL_min)/(LL_max-LL_min)), 
                           alpha=0.5)

    for ageindex in range(len(agebins)) :
        for sindex, season in enumerate(seasons) :            
            ax = fig.add_subplot(len(agebins), len(seasons), ageindex*(len(seasons))+sindex+1)
            plot_lines(ax, [float(x)/sum(raw_data[season]['infectiousness'][ageindex,:]) for x in raw_data[season]['infectiousness'][ageindex,:]], 
                       inf_bins, plotstyle='-o', linewidth=1, mycolor='#F9A11D', alpha=1)
            ax.set_xlim(0, 100)
            ax.set_title('age ' + str(theseagebins[ageindex]) + ' to ' + str(theseagebins[ageindex+1]) + ' ' + season)
            if sindex == 0 :
                ax.set_ylabel('frac pop')
            if ageindex == len(agebins)-1 :
                ax.set_xlabel('pct mos inf')
            
    plt.savefig(fname + '.pdf', format='PDF')
    plt.close(fig)

def plot_best_LL(settings, iteration, analyzer, site, samples, index_list) :

    raw_data = { 'inf_data' : load_comparison_data(settings, site, 'infectiousness_by_age_and_season'),
                'gam_inf_data' : load_comparison_data(settings, site, 'density_and_infectiousness_by_age_and_season') }

    agebins = raw_data['inf_data']['age_bins']
    inf_bins = raw_data['inf_data']['fraction_infected_bins']
    gam_bins = raw_data['gam_inf_data']['parasitemia_bins']
    gam_bins[0] = 0.005

    outpaths = [samples[site + ' outpath'][i] for i in index_list]
    seasons = analyzer['seasons']

    scale_factor = [1]*len(outpaths)
    ad_age = [100]*len(outpaths)
    min_inf = [1]*len(outpaths)
    seas_m = [1]*len(outpaths)
    paramnames = list(samples.columns.values)
    if 'Acquire_Modifier' in paramnames :
        scale_factor = [samples['Acquire_Modifier'].values[x] for x in index_list]
    if 'Age_Dependent_Decrease_In_Infectivity_Min_Infectivity' in paramnames :
        min_inf = [samples['Age_Dependent_Decrease_In_Infectivity_Min_Infectivity'].values[x] for x in index_list]
    if 'Age_Dependent_Decrease_In_Infectivity_Adult_Age' in paramnames :
        ad_age = [samples['Age_Dependent_Decrease_In_Infectivity_Adult_Age'].values[x] for x in index_list]
    if 'Seasonal_Multiplier' in paramnames :
        scale_factor = [samples['Seasonal_Multiplier'].values[x] for x in index_list]
    
    if iteration == 0 :
        plot_infectiousness(settings['plot_dir'] + site + '_reference_infectiousness', raw_data['inf_data'], agebins, inf_bins,
                            seasons, ref=True)
        plot_inf_vs_gam_density(settings['plot_dir'] + site + '_reference_inf_vs_gam_density', raw_data['gam_inf_data'], agebins, inf_bins, gam_bins,
                                seasons, ref=True)
    
    for i, outpath in enumerate(outpaths) :
        data = get_survey_report_data(outpath, ['initial_age', 'infectiousness', 'true_gametocytes'], analyzer['start_day'])
        plot_infectiousness(settings['plot_dir'] + site + '_infectiousness_LLrank' + str(i), data, agebins, inf_bins,
                            seasons, scale_factor=scale_factor[i], min_inf=min_inf[i], ad_age=ad_age[i], seas_m=seas_m[i])
        plot_inf_vs_gam_density(settings['plot_dir'] + site + '_reference_inf_vs_gam_density_LLrank' + str(i), data, agebins, inf_bins, gam_bins,
                                seasons, scale_factor=scale_factor[i], min_inf=min_inf[i], ad_age=ad_age[i], seas_m=seas_m[i])

    return

def plot_lines(ax, data, bins, plotstyle='-o', linewidth=1, mycolor='#C01E6C', alpha=1) :

    ax.plot(bins, data, plotstyle, linewidth=linewidth, color=mycolor, alpha=alpha)

def plot_inf_vs_gam_density(fname, data, agebins, inf_bins, gam_bins, seasons, scale_factor=1, min_inf=1, ad_age=100, seas_m=1, ref=False) :

    d, totalpop = {}, {}
    if ref :
        for season in seasons :
            d[season] = data[season]['Gametocytemia and Infectiousness']
            totalpop[season] = [sum(sum(d[season][x, :, :])) for x in range(len(agebins))]
        mycolor = '#F9A11D'
    else :
        for i, season in enumerate(seasons) :
            date = int(365/12.*seasons[season])
            d[season], totalpop[season] = get_gametocytemia_and_infectiousness_at_date(data, inf_bins, gam_bins, agebins, date, scale_factor, min_inf, ad_age, seas_m**i)
        mycolor = '#C01E6C'

    fig = plt.figure('Infectiousness vs Gametocyte Density by Age and Season', figsize=(11, 9))
    plt.subplots_adjust(left=0.1, right=0.95, bottom=0.1, top=0.95, hspace=0.25)

    theseagebins = [0] + agebins
    for ageindex in range(len(agebins)) :
        for sindex, season in enumerate(seasons) :
            
            ax = fig.add_subplot(len(agebins), len(seasons), ageindex*(len(seasons))+sindex+1)
            for j in range(len(inf_bins)) :
                for k in range(len(gam_bins)-1) :
                    if d[season][ageindex, k, j] > 0 :
                        ax.semilogx(gam_bins[k], inf_bins[j], 'o', markersize=50*sqrt(1.*d[season][ageindex, k, j]/(totalpop[season][ageindex])), 
                                    markerfacecolor=mycolor, alpha=0.5)

            ax.set_xlim(10**-3, 10**6)
            ax.set_ylim(0, 100)
            ax.set_title('age ' + str(theseagebins[ageindex]) + ' to ' + str(theseagebins[ageindex+1]) + ' ' + season)
            if sindex == 0 :
                ax.set_ylabel('pct mos inf')
            if ageindex == len(agebins)-1 :
                ax.set_xlabel('gam dens per uL')


    plt.savefig(fname + '.pdf', format='PDF')
    plt.close(fig)

def plot_infectiousness(fname, data, agebins, inf_bins, seasons, scale_factor=1, min_inf=1, ad_age=100, seas_m=1, ref=False) :

    if ref :
        d = {}
        for season in seasons :
            d[season] = data[season]['infectiousness']
        mycolor = '#F9A11D'
    else :
        d = {}
        for season in seasons :
            date = int(365/12.*seasons[season])
            d[season] = get_infectiousness_at_date(data, inf_bins, agebins, date, scale_factor, min_inf, ad_age, seas_m)
        mycolor = '#C01E6C'

    fig = plt.figure(fname, figsize=(3*len(seasons.keys()),4))    
    plt.subplots_adjust(hspace=0.5,bottom=0.15, right=0.95, left=0.1)

    for s, season in enumerate(seasons.keys()) :
        ax = fig.add_subplot(1,len(seasons.keys()),s+1)

        for j in range(len(agebins)) :
            for k in range(len(inf_bins)-1) :
                ax.plot(j, inf_bins[k], 'o', markersize=50*sqrt(1.*d[season][j, k]/(sum(d[season][j, :]))), 
                            markerfacecolor=mycolor, alpha=0.5)

        ax.set_ylim(0,100)
        ax.set_xlim(-1, 3)
        ax.xaxis.set_major_locator(FixedLocator(range(len(agebins))))
        ax.set_xticklabels(['<' + str(age) for age in agebins])
            
        ax.set_xlabel('age in years')
        ax.set_title(season)
        if s == 0 :
            ax.set_ylabel('percent mosquitoes infected')

    plt.savefig(fname + '.pdf', format='PDF')
    plt.close(fig)

def get_survey_report_data(simpath, channels, start_day=1) :

    simfile = 'MalariaSurveyJSONAnalyzer_Day_' + str(start_day) + '_' + str(0) + '.json'
    with open(os.path.join(simpath,'output',simfile)) as fin :
        all_data = json.loads(fin.read())
    patients = []
    for patient in all_data['patient_array'] :
        d = {}
        for channel in channels :
            if channel == 'initial_age' :
                d[channel] = patient[channel]
            else :
                d[channel] = patient[channel][0]
        patients.append(d)
    return patients

def compare_infectiousness(raw_data, sim_data, agebins, seasons, start_day=1, scale_factor=1, min_inf=1, ad_age=1, seas_m=1) :

    inf_bins = raw_data['fraction_infected_bins']
    LL = 0
    for i, season in enumerate(seasons) :
        date = int(365/12.*seasons[season])
        sim_inf = get_infectiousness_at_date(sim_data, inf_bins, agebins, date, scale_factor, min_inf, ad_age, seas_m**i)
        LL += LL_calculators.dirichlet_multinomial(raw_data[season]['infectiousness'], sim_inf)

    return LL

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

    return binned_data, totalpop

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