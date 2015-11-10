import numpy as np
import LL_calculators
from load_comparison_data import load_comparison_data
import matplotlib.pyplot as plt
import json
from parsers_malaria import get_site_data
import matplotlib.cm as cm
import pandas as pd
import math
import seaborn as sns
from scipy import stats
from utils import calc_distance, latlon_to_anon

def analyze_household_prevalence(settings, analyzer, site, data) :

    raw_data = load_comparison_data(settings, site, 'prevalence_by_node')
    burn_in = analyzer['burn_in']

    LL = [0]*len(data[0]['Population'])
    nodes = data[0]['nodeids']
    field = analyzer['fields_to_get'][0]

    for rownum in range(len(LL)) :
        prev = [[data[y][field][rownum][0][x] for x in range(len(nodes))] for y in range(settings['sim_runs_per_param_set'])] # prev for each node for one run
        sim_data = [np.mean([prev[y][x] for y in range(settings['sim_runs_per_param_set'])]) for x in range(len(nodes))]
        LL[rownum] += LL_calculators.euclidean_distance([raw_data[str(x)] for x in nodes], sim_data)
    return LL

def visualize_household_prevalence(settings, iteration, analyzer, site, samples, top_LL_index) :

    plot_best_LL(settings, iteration, site, analyzer, samples, top_LL_index)

def plot_best_LL(settings, iteration, site, analyzer, samples, top_LL_index) :

    burn_in = analyzer['burn_in']
    raw_data = load_comparison_data(settings, site, 'prevalence_by_node')

    channel = 'New_Diagnostic_Prevalence'
    date = analyzer['testdays'][0]

    for j, LL_index in enumerate(top_LL_index) :
        fname = settings['plot_dir'] + site + '_prev_v_ref_LLrank' + str(j)
        sns.set_style('white')
        fig = plt.figure(fname, figsize=(4,3))
        plt.subplots_adjust(left=0.15, bottom=0.15, right=0.95)
        prev_data = []
        pop_data = []
        for run_num in range(settings['sim_runs_per_param_set']) :
            outpath = samples[site + ' outpath ' + str(run_num)].values[LL_index]
            output = get_spatial_report_data(outpath, channel)
            nodes = output['nodeids']
            prev = [output['data'][date][x] for x in range(len(nodes))]
            output = get_spatial_report_data(outpath, 'Population')
            pop = [output['data'][date][x] for x in range(len(nodes))]
            if j == 0 and run_num == 0 :
                demodf = get_node_locations(settings, outpath)
            prev_data.append(prev)
            pop_data.append(pop)

        data = [np.mean([prev_data[y][x] for y in range(settings['sim_runs_per_param_set'])]) for x in range(len(nodes))]
        refdata = [raw_data[str(x)] for x in nodes]
        meanpop = [np.mean([pop_data[y][x] for y in range(settings['sim_runs_per_param_set'])]) for x in range(len(nodes))]

        ax = fig.add_subplot(111)    
        plot_prevs(ax, refdata, data, meanpop)
        plt.savefig(fname + '.pdf', format='PDF')
        plt.close(fig)

        mapdf = pd.DataFrame({'Population' : [np.mean([pop_data[y][x] for y in range(settings['sim_runs_per_param_set'])]) for x in range(len(nodes))],
                              'Prevalence' : [np.mean([prev_data[y][x] for y in range(settings['sim_runs_per_param_set'])]) for x in range(len(nodes))],
                              'Latitude' : demodf['Latitude'].values,
                              'Longitude' : demodf['Longitude'].values})
        plot_map(mapdf, analyzer['map_size'], 'Population', 'Prevalence')
        plt.savefig(settings['plot_dir'] + site + '_prev_map_LLrank' + str(j) + '.pdf', format='PDF')
        plt.close()


    return

def plot_prevs(ax, refdata, data, pop) :

    scale = 20
    smax = max(pop)
    smin = 0
    s = [(1.*x-smin)/(smax-smin) for x in pop]

    ax.plot([0, 1], [0, 1], 'k', alpha=0.5, linewidth=1)
    ax.scatter(refdata, data, [math.sqrt(x)*scale for x in s], 
               alpha=0.7, color='#8DC63F', edgecolor='#6D6E71')
    ax.set_xlabel('hh obs prevalence')
    ax.set_ylabel('hh sim prevalence')
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)

def plot_map(df, map_size, sizefield='', colorfield='') :

    sns.set_style('whitegrid')
    palette = sns.color_palette('RdBu_r', 200)[100:]
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
        cmin = 0
        cmax = 1
        c = [0]*len(df.index)
        notzeros = filter(lambda x : df[colorfield].values[x] != 0, range(len(df.index)))
        for x in notzeros :
            c[x] = int(min([99,(df[colorfield].values[x]-cmin)/(cmax-cmin)*99]))
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

    from parsers_malaria import load_bin_file
    simfile = 'SpatialReport_' + channel + '.bin'
    spatial_data = load_bin_file(outpath + '/output/' + simfile)

    return spatial_data

def get_node_locations(settings, outpath) :

    with open(outpath + '/config.json') as fin :
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
