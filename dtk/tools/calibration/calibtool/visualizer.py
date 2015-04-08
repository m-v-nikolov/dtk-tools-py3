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

def visualize(settings, iteration, analyzers, sites=[], num_param_sets=1) :

    plot_site_data(settings, iteration, analyzers, sites, num_param_sets)
    plot_likelihoods_by_parameter(settings, iteration)

def plot_site_data(settings, iteration, analyzers, sites, num_param_sets) :

    with open(settings['curr_iteration_dir'] + 'LL.json') as fin :
        samples = json.loads(fin.read())
    with open(settings['curr_iteration_dir'] + 'params_withpaths.json') as fin :
        t = json.loads(fin.read())
        for key in t.keys() :
            if 'outpath' in key :
                samples[key] = t[key]

    from operator import itemgetter
    d = sorted([(item, i) for i, item in enumerate(samples['LL'])], key=itemgetter(0), reverse=True)
    top_LL_index = [x[1] for x in d][:num_param_sets]

    if sites == [] :
        sites = settings['sites'].keys()

    for site in sites :
        if settings['sim_type'] == 'MALARIA_SIM' :
            visualize_malaria_sim(settings, iteration, analyzers, site, samples, top_LL_index)

def plot_likelihoods_by_parameter(settings, iteration) :

    with open(settings['initial_sampling_range_file']) as fin :
        samplerange = json.loads(fin.read())
    paramnames = samplerange.keys()

    color = ['#4BB5C1']*(iteration+1)
    color[-1] = '#FF2D00'

    for par in paramnames :
        fig = plt.figure('LL by parameter ' + par, figsize=(5,4))
        ax = fig.add_subplot(111)
        plt.subplots_adjust(left=0.15, bottom=0.15)
        for i in range(iteration+1) :
            with open(settings['exp_dir'] + 'iter' + str(i) + '/' + 'LL.json') as fin :
                samples = json.loads(fin.read())

            plot_1D_likelihood(samplerange[par], samples[par], samples['LL'], color=color[i], linewidth=(i+1)/(iteration+1.)*2, alpha=(i+1)/(iteration+1.))

            if 'log' in samplerange[par]['type'] :
                ax.set_xscale('log')
            ax.set_xlim(samplerange[par]['min'], samplerange[par]['max'])

            ax.set_xlabel(par)
            ax.set_ylabel('log likelihood')

        plt.savefig(settings['curr_iteration_dir'] + 'LL_' + par + '.pdf', format='PDF')
        plt.close(fig)

def plot_1D_likelihood(par_settings, parvalues, LLvalues, color='k', linewidth=1, alpha=1) :

    x, y = [], []
    sindex = sorted(range(len(parvalues)), key=lambda k: parvalues[k])
    for i in sindex :
        x.append(parvalues[i])
        y.append(LLvalues[i])

    plt.plot(x, y, color=color, linewidth=linewidth, alpha=alpha)

def visualize_malaria_sim(settings, iteration, analyzers, site, samples, top_LL_index) :

    from analyze_seasonal_monthly_density import visualize_seasonal_monthly_density
    from analyze_malariatherapy_density import visualize_malariatherapy_density
    from analyze_malariatherapy_duration import visualize_malariatherapy_duration
    from analyze_seasonal_infectiousness import visualize_seasonal_infectiousness
    from analyze_prevalence_by_age import visualize_prevalence_by_age
    from analyze_clinical_incidence_by_age import visualize_clinical_incidence_by_age

    for this_analyzer in settings['sites'][site] :
        if this_analyzer == 'prevalence_by_age_analyzer' :
            visualize_prevalence_by_age(settings, iteration, analyzers[this_analyzer], 
                                        site, samples, top_LL_index)
        if this_analyzer == 'annual_clinical_incidence_by_age_analyzer' :
            visualize_clinical_incidence_by_age(settings, iteration, analyzers[this_analyzer], 
                                                site, samples, top_LL_index)
        if this_analyzer == 'seasonal_monthly_density_analyzer' :
            visualize_seasonal_monthly_density(settings, iteration, analyzers[this_analyzer], 
                                                site, samples, top_LL_index)
        if this_analyzer == 'seasonal_infectiousness_analyzer' :
            visualize_seasonal_infectiousness(settings, iteration, analyzers[this_analyzer], 
                                                site, samples, top_LL_index)
        if this_analyzer == 'malariatherapy_density_analyzer' :
            visualize_malariatherapy_density(settings, iteration, analyzers[this_analyzer], site, samples, top_LL_index)
        if this_analyzer == 'malariatherapy_duration_analyzer' :
            visualize_malariatherapy_duration(settings, iteration, analyzers[this_analyzer], site, samples, top_LL_index)

