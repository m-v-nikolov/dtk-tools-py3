import os

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.ticker import FixedLocator
import pandas as pd
import json
import math
import seaborn as sns

from dtk.calibration.utils import calc_distance, latlon_to_anon
from dtk.calibration import LL_calculators
from dtk.calibration.study_sites.set_calibration_site import get_reference_data


def analyze_prevalence_risk(settings, analyzer, site, data, samples) :

    LL_fn = getattr(LL_calculators, analyzer['LL_fn'])
    raw_data = get_reference_data(site, 'risk_by_distance')
    distances = raw_data['distances']
    raw_risk_data = raw_data['risks'] + [raw_data['prevalence']]
    
    field = analyzer['fields_to_get'][0]
    LL = [0]*len(samples.index)
    nodes = data[0]['nodeids']
    dist_mat = distance_df(settings, analyzer, samples.ix[0, site + ' outpath 0'])
    #dist_mat.to_csv('C:/Users/jgerardin/work/households_as_nodes/calibtool_distmat.csv', index=False)

    record_data_by_sample = { 'risk_by_distance' : [], 'Population' : [], 'Prevalence' : [] }
    for rownum in range(len(LL)) :
        sim_data = []
        prevdata = []
        popdata = []
        for y in range(settings['sim_runs_per_param_set']) :
            prev = [data[y][field][rownum][0][x] for x in range(len(nodes)) if nodes[x] not in analyzer['worknode']] # prev for each node for one run
            pop = [data[y]['Population'][rownum][0][x] for x in range(len(nodes)) if nodes[x] not in analyzer['worknode']] # pop for each node for one run

            df = pd.DataFrame({'ids' : filter(lambda x : x not in analyzer['worknode'], nodes), 'pop' : pop, 'pos' : [prev[x]*pop[x] for x in range(len(nodes)) if nodes[x] not in analyzer['worknode']]})
            sim_data_run = get_relative_risk_by_distance(df, dist_mat, distances)
            sim_data_run.append(sum(df['pos'].values)/sum(df['pop'].values))

            prevdata.append(prev)
            popdata.append(pop)

            sim_data.append(sim_data_run)

        mean_sim_data = [np.mean([sim_data[y][x] for y in range(settings['sim_runs_per_param_set'])]) for x in range(len(raw_risk_data))]
        LL[rownum] += LL_fn(raw_risk_data, mean_sim_data)
        record_data_by_sample['risk_by_distance'].append(mean_sim_data)
        record_data_by_sample['Population'].append([np.mean([popdata[y][x] for y in range(settings['sim_runs_per_param_set'])]) for x in range(len(nodes)) if nodes[x] not in analyzer['worknode']])
        record_data_by_sample['Prevalence'].append([np.mean([prevdata[y][x] for y in range(settings['sim_runs_per_param_set'])]) for x in range(len(nodes)) if nodes[x] not in analyzer['worknode']])

    with open(os.path.join(settings['curr_iteration_dir'],site + '_' + analyzer['name'] + '.json'), 'w') as fout :
        json.dump(record_data_by_sample, fout)
    return LL

def visualize_prevalence_risk(settings, iteration, analyzer, site, samples, top_LL_index) :

    plot_best_LL(settings, iteration, site, analyzer, samples, top_LL_index)
    plot_all_LL(settings, iteration, site, analyzer, samples)

def plot_best_LL(settings, iteration, site, analyzer, samples, top_LL_index) :
        
    raw_data = get_reference_data(site, 'risk_by_distance')
    distances = raw_data['distances']
    raw_risk_data = raw_data['risks'] + [raw_data['prevalence']]

    for j, LL_index in enumerate(top_LL_index) :
        fname = os.path.join(settings['plot_dir'],site + '_risk_of_rdtpos_LLrank' + str(j))
        sns.set_style('white')
        fig = plt.figure(fname, figsize=(4,3))
        plt.subplots_adjust(left=0.15, bottom=0.15, right=0.95)
        ax = fig.add_subplot(111)    

        iter = samples['iteration'].values[LL_index]
        prevsamples = len(samples[samples['iteration'] < iter].index)
        rownum = LL_index-prevsamples
        with open(os.path.join(settings['exp_dir'], 'iter' + str(iter) + '/' + site + '_' + analyzer['name']) + '.json') as fin :
            data = json.loads(fin.read())
        plot_risks(ax, data['risk_by_distance'][rownum], distances, style='-o', color='#CB5FA4', alpha=1, linewidth=1)
        plot_risks(ax, raw_risk_data, distances, style='-o', color='#8DC63F', alpha=1, linewidth=1)
        plt.savefig(fname + '.pdf', format='PDF')
        plt.close(fig)

        if j == 0 :
            outpath = samples[site + ' outpath 0'].values[LL_index]
            demodf = get_node_locations(settings, outpath, analyzer['worknode'])

        mapdf = pd.DataFrame({'Population' : data['Population'][rownum],
                              'Prevalence' : data['Prevalence'][rownum],
                              'Latitude' : demodf['Latitude'].values,
                              'Longitude' : demodf['Longitude'].values})
        plot_map(mapdf, analyzer['map_size'], 'Population', 'Prevalence')
        plt.savefig(os.path.join(settings['plot_dir'],site + '_prev_map_LLrank' + str(j) + '.pdf'), format='PDF')
        plt.close()


def plot_all_LL(settings, iteration, site, analyzer, samples) :

    raw_data = get_reference_data(site, 'risk_by_distance')
    distances = raw_data['distances']
    raw_risk_data = raw_data['risks'] + [raw_data['prevalence']]

    LL = samples['LL'].values
    LL_max = max(LL)
    LL_min = min(LL)
    if LL_min == LL_max : LL_min = LL_max-1

    fname = os.path.join(settings['plot_dir'],site + '_risk_of_rdtpos_all')
    sns.set_style('white')
    fig = plt.figure(fname, figsize=(4,3))
    plt.subplots_adjust(left=0.15, bottom=0.15, right=0.95)
    ax = fig.add_subplot(111)    

    grouped = samples.groupby('iteration')
    prevsamples = 0
    for i, (iter, df_iter) in enumerate(grouped) :
        with open(os.path.join(settings['exp_dir'], 'iter' + str(iter) + '/' + site + '_' + analyzer['name']) + '.json') as fin :
            data = json.loads(fin.read())['risk_by_distance']
        for rownum, sim_data in enumerate(data) :
            plot_risks(ax, sim_data, distances, style='-', color=cm.Blues((LL[rownum + prevsamples]-LL_min)/(LL_max-LL_min)), alpha=0.5, linewidth=0.5)
        prevsamples += len(df_iter.index)
    plot_risks(ax, raw_risk_data, distances, style='-o', color='#8DC63F', alpha=1, linewidth=1)
    plt.savefig(fname + '.pdf', format='PDF')
    plt.close(fig)

def plot_risks(ax, risk_data, distances, style='-o', color='#CB5FA4', alpha=0.5, linewidth=0.5) :

    ax.plot(range(len(risk_data)), risk_data, style, color=color, alpha=alpha, linewidth=linewidth) 

    ax.xaxis.set_major_locator(FixedLocator(range(len(risk_data))))
    ax.set_xticklabels(['hh'] + [str(x) for x in distances[1:]] + ['all'])
    ax.set_ylim(0,0.3)
    ax.set_ylabel('prob rdt pos')
    ax.set_xlim(-0.1, len(risk_data)-1+0.1)

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
            #df = df[df[sizefield] > 0]
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
               [math.sqrt(x)*scale+5 for x in s], 
               facecolor=[palette[x] for x in c], edgecolor='#6D6E71',
               linewidth=0.5, alpha=0.5)
    ax.set_xlim(-1*map_size, map_size)
    ax.set_ylim(-1*map_size, map_size)
    ax.set_xticklabels([])
    ax.set_yticklabels([])

def get_demographics(settings, outpath) :

    with open(os.path.join(outpath, 'config.json')) as fin :
        config = json.loads(fin.read())['parameters']
    if settings['run_location'] == '' :
        demofile = settings['local_input_root'] + config['Demographics_Filenames'][0]
    else :
        demofile = settings['hpc_input_root'] + config['Demographics_Filenames'][0]

    with open(demofile) as fin :
        return json.loads(fin.read())

def get_node_locations(settings, outpath, worknode) :

    t = get_demographics(settings, outpath)['Nodes']
    demo = [x['NodeAttributes'] for x in t]
    for i in range(len(demo)) :
        demo[i]['NodeID'] = t[i]['NodeID']
    demo = filter(lambda x : x['NodeID'] not in worknode, demo)
    demo = pd.DataFrame(demo)
    return demo

def distance_df(settings, analyzer, outpath) :

    demo = get_demographics(settings, outpath)

    lats = []
    lons = []
    nodeids = []
    for node in demo['Nodes'] :
        if node['NodeID'] not in analyzer['worknode'] :
            nodeids.append(node['NodeID'])
            lats.append(node['NodeAttributes']['Latitude'])
            lons.append(node['NodeAttributes']['Longitude'])
    n1 = []
    n2 = []
    d = []
    for i in range(len(nodeids)) :
        for j in range(len(nodeids)) :
            n1.append(nodeids[i])
            n2.append(nodeids[j])
            d.append(calc_distance(lats[i], lons[i], lats[j], lons[j]))
    return pd.DataFrame({'node1' : n1, 'node2' : n2, 'dist' : d})

def get_relative_risk_by_distance(df, ddf, distances) :

    nodelist = df['ids'].values.tolist()
    rel_risk = []
    for k, n_dist in enumerate(distances) :
        pos_w_pos = 0.
        tot_w_pos = 0.
        for hh_num in df.index :
            if df.ix[hh_num, 'pos'] < 1 :
                continue
            
            if n_dist == 0 and df.ix[hh_num, 'pop'] > 1 :
                hh_pos = df.ix[hh_num, 'pos']
                hh_tot = df.ix[hh_num, 'pop']
                num_pos = (hh_pos - 1)*hh_pos
                num_ppl = (hh_tot - 1)*hh_pos

            else :
                # node IDs of nodes within distance
                neighbors = ddf[(ddf['node1'] == nodelist[hh_num]) & (ddf['node2'] != nodelist[hh_num]) &
                                (ddf['dist'] <= n_dist) & (ddf['dist'] > distances[k-1])]['node2'].values

                ndf = df[df['ids'].isin(neighbors)]
                num_pos = sum(ndf['pos'].values)
                num_ppl = sum(ndf['pop'].values)

            pos_w_pos += num_pos
            tot_w_pos += num_ppl
        if tot_w_pos > 0 :
            rel_risk.append(pos_w_pos/tot_w_pos)
        else :
            rel_risk.append(0)
    return rel_risk