#####################################################################
# visualizer.py
#
#
# plot_site_data()
# ---
# Calls site and analyzer-specific plotters. Default plots simulated data for single parameter sample with highest likelihood.
#
# plot_likelihoods_by_parameter()
# ---
# Plots log likelihood over each sampled parameter for current and all previous iterations.
#
#####################################################################

import json
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

def visualize(settings, iteration, analyzers, sites=[], num_param_sets=1) :

    sns.set_style('white')
    plot_site_data(settings, iteration, analyzers, sites, num_param_sets)    
    if settings['combine_site_likelihoods'] :
        plot_likelihoods_by_parameter(settings, iteration)
    else :
        plot_likelihoods_by_parameter_and_site(settings, iteration)

def plot_site_data(settings, iteration, analyzers, sites, num_param_sets) :
    
    samples = pd.read_csv(settings['exp_dir'] + 'LL_all.csv')
    if sites == [] :
        sites = settings['sites'].keys()

    from operator import itemgetter
    if settings['combine_site_likelihoods'] :
        LLs = samples['LL'].values
        d = sorted([(item, i) for i, item in enumerate(LLs)], key=itemgetter(0), reverse=True)
        top_LL_index = [x[1] for x in d][:num_param_sets]
        for site in sites :
            if settings['sim_type'] == 'MALARIA_SIM' :
                visualize_malaria_sim(settings, iteration, analyzers, site, samples, top_LL_index)
    else :
        for site in sites :
            LLs = samples['LL ' + site].values
            d = sorted([(item, i) for i, item in enumerate(LLs)], key=itemgetter(0), reverse=True)
            top_LL_index = [x[1] for x in d][:num_param_sets]
            if settings['sim_type'] == 'MALARIA_SIM' :
                visualize_malaria_sim(settings, iteration, analyzers, site, samples, top_LL_index)

def plot_likelihoods_by_parameter(settings, iteration) :

    initial_sampling_range_file = settings['initial_sampling_range_file']
    samplerange = pd.read_csv(initial_sampling_range_file)
    paramnames = samplerange['parameter'].values

    color = ['#4BB5C1']*(iteration+1)
    color[-1] = '#FF2D00'

    for pnum, par in enumerate(paramnames) :
        if 'HABSCALE' in par :
            continue
        fig = plt.figure('LL by parameter ' + par, figsize=(5,4))
        ax = fig.add_subplot(111)
        plt.subplots_adjust(left=0.15, bottom=0.15)
        samples = pd.read_csv(settings['exp_dir'] + 'LL_all.csv')
        for i in range(iteration+1) :
            mysamples = samples[samples['iteration'] == i]
            plot_1D_likelihood(mysamples[par].values, mysamples['LL'].values, color=color[i], linewidth=(i+1)/(iteration+1.)*2, alpha=(i+1)/(iteration+1.))

            if 'log' in samplerange.ix[pnum, 'type'] :
                ax.set_xscale('log')
            ax.set_xlim(samplerange.ix[pnum, 'min'], samplerange.ix[pnum, 'max'])

            ax.set_xlabel(par)
            ax.set_ylabel('log likelihood')

        plt.savefig(settings['curr_iteration_dir'] + 'LL_' + par + '.pdf', format='PDF')
        plt.savefig(settings['plot_dir'] + 'LL_' + par + '.pdf', format='PDF')
        plt.close(fig)

def plot_likelihoods_by_parameter_and_site(settings, iteration) :

    sites = settings['sites'].keys()

    initial_sampling_range_file = settings['exp_dir'] + 'iter0/initial_sampling_range.json'
    samplerange = pd.read_csv(initial_sampling_range_file)
    paramnames = samplerange['parameter'].values

    color = ['#4BB5C1']*(iteration+1)
    color[-1] = '#FF2D00'

    for site in sites :
        for pnum, par in enumerate(paramnames) :
            fig = plt.figure(site + ' LL by parameter ' + par, figsize=(5,4))
            ax = fig.add_subplot(111)
            plt.subplots_adjust(left=0.15, bottom=0.15)
            samples = pd.read_csv(settings['exp_dir'] + 'LL_all.csv')
            for i in range(iteration+1) :
                mysamples = samples[samples['iteration'] == i]
                plot_1D_likelihood(mysamples[par].values, mysamples['LL ' + site].values, color=color[i], linewidth=(i+1)/(iteration+1.)*2, alpha=(i+1)/(iteration+1.))

                if 'log' in samplerange.ix[pnum, 'type'] :
                    ax.set_xscale('log')
                ax.set_xlim(samplerange.ix[pnum, 'min'], samplerange.ix[pnum, 'max'])

                ax.set_xlabel(par)
                ax.set_ylabel('log likelihood')

            plt.savefig(settings['curr_iteration_dir'] + site + ' LL_' + par + '.pdf', format='PDF')
            plt.savefig(settings['plot_dir'] + site + ' LL_' + par + '.pdf', format='PDF')
            plt.close(fig)

def plot_1D_likelihood(parvalues, LLvalues, color='k', linewidth=1, alpha=1) :

    x, y = [], []
    sindex = sorted(range(len(parvalues)), key=lambda k: parvalues[k])
    for i in sindex :
        x.append(parvalues[i])
        y.append(LLvalues[i])

    plt.plot(x, y, color=color, linewidth=linewidth, alpha=alpha)

def visualize_malaria_sim(settings, iteration, analyzers, site, samples, top_LL_index) :

    import importlib
    import sys
    sys.path.append(settings['calibtool_dir'] + 'analyzers/')

    for this_analyzer in settings['sites'][site] :

        mod = importlib.import_module(analyzers[this_analyzer]['name'])
        an_fn = getattr(mod, analyzers[this_analyzer]['name'].replace('analyze', 'visualize'))
        an_fn(settings, iteration, analyzers[this_analyzer], site, samples, top_LL_index)

