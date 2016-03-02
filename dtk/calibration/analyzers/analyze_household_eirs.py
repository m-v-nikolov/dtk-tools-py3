import os

import numpy as np

import matplotlib.pyplot as plt
import json

import matplotlib.cm as cm
import pandas as pd
import math
import seaborn as sns
from dtk.calibration.load_comparison_data import load_comparison_data
from scipy import stats

from dtk.calibration.utils import latlon_to_anon


def analyze_household_eirs(settings, analyzer, site, data) :

    raw_data = load_comparison_data(settings, site, 'annual_eir')
    burn_in = analyzer['burn_in']

    LL = [0]*len(data[0]['Daily_EIR'])
    nodes = data[0]['nodeids']

    for field in analyzer['fields_to_get'] :
        for rownum in range(len(LL)) :
            sim_data = [np.mean([sum([data[y][field][rownum][z][x] for z in range(-365,0)]) for y in range(settings['sim_runs_per_param_set'])]) for x in range(len(nodes))]
            #"""
            slope, intercept, r_value, p_value, std_err = stats.linregress([raw_data[str(x)] for x in nodes], sim_data)
            LL[rownum] += -1*((slope-1)**2)*(1-r_value)
            #"""
            #LL[rownum] += LL_calculators.weighted_squares([raw_data[str(x)] for x in nodes], sim_data)
    return LL

def visualize_household_eirs(settings, iteration, analyzer, site, samples, top_LL_index) :

    plot_best_LL(settings, iteration, site, analyzer, samples, top_LL_index)

def plot_best_LL(settings, iteration, site, analyzer, samples, top_LL_index) :

    burn_in = analyzer['burn_in']
    raw_data = load_comparison_data(settings, site, 'annual_eir')

    channel = 'Daily_EIR'

    for j, LL_index in enumerate(top_LL_index) :
        fname = os.path.join(settings['plot_dir'], site + '_eirs_v_ref_LLrank' + str(j))
        sns.set_style('white')
        fig = plt.figure(fname, figsize=(4,3))
        plt.subplots_adjust(left=0.15, bottom=0.15, right=0.95)
        data_by_run = []
        pop = []
        for run_num in range(settings['sim_runs_per_param_set']) :
            outpath = samples[site + ' outpath ' + str(run_num)].values[LL_index]
            output = get_spatial_report_data(outpath, channel)
            if j == 0 and run_num == 0 :
                demodf = get_node_locations(settings, outpath)
            nodes = output['nodeids']
            data_by_run.append(output['data'])
            output = get_spatial_report_data(outpath, 'Population')['data']
            pop.append([np.mean([output[x][y] for x in range(-365,0)]) for y in range(len(nodes))])

        data = [np.mean([sum([data_by_run[y][z][x] for z in range(-365,0)]) for y in range(settings['sim_runs_per_param_set'])]) for x in range(len(nodes))]
        refdata = [raw_data[str(x)] for x in nodes]
        meanpop = [np.mean([pop[y][x] for y in range(settings['sim_runs_per_param_set'])]) for x in range(len(nodes))]

        ax = fig.add_subplot(111)    
        plot_eirs(ax, refdata, data, meanpop)
        plt.savefig(fname + '.pdf', format='PDF')
        plt.close(fig)

        for i in range(len(demodf.index)) :
            demodf.ix[i, 'Population'] = meanpop[i]
            demodf.ix[i, 'Annual_EIR'] = data[i]
        plot_eir_map(demodf, analyzer['map_size'], 'Population', 'Annual_EIR')
        plt.savefig(os.path.join(settings['plot_dir'],site + '_eirs_map_LLrank' + str(j) + '.pdf'), format='PDF')
        plt.close()

    return

def plot_eirs(ax, refdata, data, pop) :

    scale = 200
    smax = max(pop)
    smin = 0
    s = [(1.*x-smin)/(smax-smin) for x in pop]

    ax.plot([0, 20], [0, 20], 'k', alpha=0.5, linewidth=1)
    ax.scatter(refdata, data, [math.sqrt(x)*scale for x in s], 
               alpha=0.7, color='#8DC63F', edgecolor='#6D6E71')
    ax.set_xlabel('hh fitted EIR')
    ax.set_ylabel('hh as nodes sim EIR')
    ax.set_xlim(-1,21)
    ax.set_ylim(-1,)

def plot_eir_map(df, map_size, sizefield='', colorfield='') :

    sns.set_style('whitegrid')
    palette = sns.color_palette('RdBu_r', 100)
    scale = 200

    if sizefield != '' :
        if len(list(set(df[sizefield].values))) == 1 :
            s = [1]*len(df.index)
        else :
            smin = 0
            smax = max(df[sizefield].values)
            df = df[df[sizefield] > 0]
            s = [(1.*x-smin)/(smax-smin) for x in df[sizefield].values]
    else :
        s = [1]*len(df.index)
    if colorfield != '' :
        cmin = -2
        cmax = 2
        c = [0]*len(df.index)
        notzeros = filter(lambda x : df[colorfield].values[x] != 0, range(len(df.index)))
        for x in notzeros :
            c[x] = int(min([99,(math.log10(df[colorfield].values[x])-cmin)/(cmax-cmin)*99]))
    else :
        c = [50]*len(df.index)

    fig = plt.figure(figsize=(8,7))
    ax = fig.add_subplot(111)
    xcoords, ycoords = latlon_to_anon(df['Latitude'].values, 
                                      df['Longitude'].values)

    ax.scatter(xcoords, ycoords,
               [math.sqrt(x)*scale for x in s], 
               facecolor=[palette[x] for x in c], edgecolor='#6D6E71',
               linewidth=0.5, alpha=0.5)
    ax.set_xlim(-1*map_size, map_size)
    ax.set_ylim(-1*map_size, map_size)
    ax.set_xticklabels([])
    ax.set_yticklabels([])

def get_spatial_report_data(outpath, channel) :

    simfile = 'SpatialReport_' + channel + '.bin'
    from dtk.calibration.parsers_malaria import load_bin_file
    spatial_data = load_bin_file(os.path.join(outpath,'output',simfile))

    return spatial_data

def get_node_locations(settings, outpath) :

    with open(os.path.join(outpath, 'config.json')) as fin :
        config = json.loads(fin.read())['parameters']
    if settings['run_location'] == '' :
        demofile = settings['local_input_root'] + config['Demographics_Filenames'][0]
    else :
        demofile = settings['hpc_input_root'] + config['Demographics_Filenames'][0]

    with open(demofile) as fin :
        t = json.loads(fin.read())['Nodes']
        demo = [x['NodeAttributes'] for x in t]
        for i in range(len(demo)) :
            demo[i]['NodeID'] = t[i]['NodeID']
            for key in t[i]['NodeAttributes']['LarvalHabitatMultiplier'] :
                demo[i][key] = t[i]['NodeAttributes']['LarvalHabitatMultiplier'][key]
    demo = pd.DataFrame(demo)
    return demo
