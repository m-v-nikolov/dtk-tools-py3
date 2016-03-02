# Template script for analyzing and visualizing simulation output from calibtool
#
# Replace all instances of TEMPLATE with new analyzer name.
# Replace all instances of DATATYPE with data descriptor
#
#
import os

import numpy as np

import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.ticker import FixedLocator
import pandas as pd
import json
import math
import seaborn as sns
from analyze_prevalence_risk import distance_df, get_relative_risk_by_distance
from dtk.calibration import LL_calculators
from dtk.calibration.study_sites.set_calibration_site import get_reference_data


def analyze_prevalence_by_node(settings, analyzer, site, data, samples) :

    LL_fn = getattr(LL_calculators, analyzer['LL_fn'])
    raw_data = get_reference_data(site, 'prevalence_by_node')
    distances = get_reference_data(site, 'risk_by_distance')['distances']
    
    field = analyzer['fields_to_get'][0]
    LL = [0]*len(samples.index)

    nodes = data[0]['nodeids']
    dist_mat = distance_df(settings, samples.ix[0, site + ' outpath 0'])

    record_data_by_sample = { 'risk_by_distance' : [], 'Population' : [], 'Prevalence' : [] }
    for rownum in range(len(LL)) :
        sim_data = []
        prevdata = []
        popdata = []
        for y in range(settings['sim_runs_per_param_set']) :
            prev = [data[y][field][rownum][0][x] for x in range(len(nodes))] # prev for each node for one run
            pop = [data[y]['Population'][rownum][0][x] for x in range(len(nodes))] # pop for each node for one run

            df = pd.DataFrame({'ids' : nodes, 'pop' : pop, 'pos' : [prev[x]*pop[x] for x in range(len(nodes))]})
            sim_data_run = get_relative_risk_by_distance(df, dist_mat, distances)
            sim_data_run.append(sum(df['pos'].values)/sum(df['pop'].values))

            prevdata.append(prev)
            popdata.append(pop)

            sim_data.append(sim_data_run)

        mean_risk_data = [np.mean([sim_data[y][x] for y in range(settings['sim_runs_per_param_set'])]) for x in range(len(distances)+1)]
        mean_prev_data = [np.mean([prevdata[y][x] for y in range(settings['sim_runs_per_param_set'])]) for x in range(len(nodes))]
        LL[rownum] += LL_fn([raw_data[str(x)] for x in nodes], mean_prev_data)

        record_data_by_sample['risk_by_distance'].append(mean_risk_data)
        record_data_by_sample['Population'].append([np.mean([popdata[y][x] for y in range(settings['sim_runs_per_param_set'])]) for x in range(len(nodes))])
        record_data_by_sample['Prevalence'].append(mean_prev_data)
    record_data_by_sample['nodeids'] = nodes

    with open(os.path.join(settings['curr_iteration_dir'],site + '_' + analyzer['name'] + '.json'), 'w') as fout :
        json.dump(record_data_by_sample, fout)
    return LL

def visualize_prevalence_by_node(settings, iteration, analyzer, site, samples, top_LL_index) :

    from analyze_prevalence_risk import visualize_prevalence_risk
    visualize_prevalence_risk(settings, iteration, analyzer, site, samples, top_LL_index)
    plot_best_LL(settings, iteration, site, analyzer, samples, top_LL_index)

def plot_best_LL(settings, iteration, site, analyzer, samples, top_LL_index) :

    raw_data = get_reference_data(site, 'prevalence_by_node')

    for j, LL_index in enumerate(top_LL_index) :
        fname = settings['plot_dir'] + site + '_prev_v_ref_LLrank' + str(j)
        sns.set_style('white')
        fig = plt.figure(fname, figsize=(4,3))
        plt.subplots_adjust(left=0.15, bottom=0.15, right=0.95)
        ax = fig.add_subplot(111)    

        iter = samples['iteration'].values[LL_index]
        prevsamples = len(samples[samples['iteration'] < iter].index)
        rownum = LL_index-prevsamples
        with open(os.path.join(settings['exp_dir'],'iter' + str(iter),site + '_' + analyzer['name'] + '.json')) as fin :
            data = json.loads(fin.read())
        if j == 0 :
            nodes = data['nodeids']
        plot_prevs(ax, [raw_data[str(x)] for x in nodes], data['Prevalence'][rownum], data['Population'][rownum])
        plt.savefig(fname + '.pdf', format='PDF')
        plt.close(fig)
    
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
