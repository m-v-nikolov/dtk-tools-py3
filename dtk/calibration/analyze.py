#####################################################################
# analyze.py
#
# Calls parser and specific analyzers for each site; combines log
# likelihoods for multi-site experiment; returns dictionary of sampled
# parameters and log likelihoods; writes sampled params and log
# likelihoods to csv file in current working directory
#
# analyze()
# ---
# 
# args : calibration settings, analyzer settings, iteration number,
# optional argument of which site(s) to analyze (otherwise analyze all
# sites in experiment)
#
# return : dictionary of sampled parameters and combined multi-site
# log likelihood for each parameter set
#
#####################################################################
import os

from load_parameters import load_samples
from utils import write_to_file
import pandas as pd

def analyze(settings, analyzers, iteration, sites=[]) :

    outfile = os.path.join(settings['curr_iteration_dir'],'LL.csv')
    try :
        samples = pd.read_csv(outfile)

    except IOError :

        if iteration == 0 :
            numsamples = settings['num_initial_samples']
        else :
            numsamples = settings['num_samples_per_iteration']

        if sites == [] :
            sites = settings['sites'].keys()

        if settings['combine_site_likelihoods'] :
            LL = [0]*numsamples
        else :
            LL = {}
        for site in sites :
            if site not in settings['sites'] :
                print 'site ' + site + ' not simulated'
                continue
            print 'analyzing site ' + site

            if settings['sim_type'] == 'MALARIA_SIM' :
                site_LL = analyze_malaria_sim(settings, analyzers, site, iteration, numsamples)
            else :
                site_LL = [0]*numsamples

            if settings['combine_site_likelihoods'] :
                for i in range(numsamples) :
                    LL[i] += site_LL[i]
            else :
                LL[site] = site_LL
           
        samples = pd.read_csv(os.path.join(settings['curr_iteration_dir'],'params_withpaths.csv'))
        if settings['combine_site_likelihoods'] :
            samples['LL'] = pd.Series(LL)
        else :
            for site in sites :
                samples['LL ' + site] = pd.Series(LL[site])
        write_to_file(samples, outfile)

    return samples

def analyze_malaria_sim(settings, analyzers, site, iteration, numsamples) :

    import importlib
    import sys
    sys.path.append(os.path.join(settings['calibtool_dir'],'analyzers'))
    from parsers_malaria import get_site_data

    LL = [0]*numsamples
    data = get_site_data(settings, analyzers, site, iteration)
    samples = pd.read_csv(os.path.join(settings['curr_iteration_dir'],'params_withpaths.csv'))
    for this_analyzer in settings['sites'][site] :

        mod = importlib.import_module("."+analyzers[this_analyzer]['name'], "dtk.calibration.analyzers")
        an_fn = getattr(mod, analyzers[this_analyzer]['name'])
        single_LL = an_fn(settings, analyzers[this_analyzer], site, data[this_analyzer], samples)

        if settings['weight_by_site'] and site in settings['weight_by_site'] and this_analyzer in settings['weight_by_site'][site] :
            for i in range(numsamples) :
                LL[i] += single_LL[i]*settings['weight_by_site'][site][this_analyzer]
        else :
            for i in range(numsamples) :
                LL[i] += single_LL[i]

    return LL



