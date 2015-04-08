#####################################################################
# analyze.py
#
# Calls parser and specific analyzers for each site; combines log
# likelihoods for multi-site experiment; returns dictionary of sampled
# parameters and log likelihoods; writes sampled params and log
# likelihoods to json file in current working directory
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

from load_parameters import load_samples
from utils import write_to_file
import json

def analyze(settings, analyzers, iteration, sites=[]) :

    outfile = settings['curr_iteration_dir'] + 'LL'
    try :
        with open(outfile + '.json') as fin :
            samples = json.loads(fin.read())

    except IOError :

        if iteration == 0 :
            numsamples = settings['num_initial_samples']
        else :
            numsamples = settings['num_samples_per_iteration']

        if sites == [] :
            sites = settings['sites'].keys()

        LL = [0]*numsamples
        for site in sites :
            if site not in settings['sites'] :
                print 'site ' + site + ' not simulated'
                continue
            print 'analyzing site ' + site

            if settings['sim_type'] == 'MALARIA_SIM' :
                site_LL = analyze_malaria_sim(settings, analyzers, site, iteration, numsamples)
            else :
                site_LL = [0]*numsamples

            for i in range(numsamples) :
                LL[i] += site_LL[i]

        with open(settings['curr_iteration_dir'] + 'params_withpaths.json') as fin :
            samples = json.loads(fin.read())
        samples['LL'] = LL
        write_to_file(samples, outfile, types=['json', 'txt'])

    return samples

def analyze_malaria_sim(settings, analyzers, site, iteration, numsamples) :

    from parsers_malaria import get_site_data
    from analyze_seasonal_monthly_density import analyze_seasonal_monthly_density
    from analyze_malariatherapy_density import analyze_malariatherapy_density
    from analyze_malariatherapy_duration import analyze_malariatherapy_duration
    from analyze_prevalence_by_age import analyze_prevalence_by_age
    from analyze_clinical_incidence_by_age import analyze_clinical_incidence_by_age
    from analyze_seasonal_infectiousness import analyze_seasonal_infectiousness

    LL = [0]*numsamples
    data = get_site_data(settings, analyzers, site, iteration)
    for this_analyzer in settings['sites'][site] :
        if this_analyzer == 'seasonal_monthly_density_analyzer' :
            single_LL = analyze_seasonal_monthly_density(analyzers[this_analyzer], site, data[this_analyzer])
        elif this_analyzer == 'prevalence_by_age_analyzer' :
            single_LL = analyze_prevalence_by_age(analyzers[this_analyzer], site, data[this_analyzer])
        elif this_analyzer == 'annual_clinical_incidence_by_age_analyzer' :
            single_LL = analyze_clinical_incidence_by_age(analyzers[this_analyzer], site, data[this_analyzer])
        elif this_analyzer == 'malariatherapy_density_analyzer' :
            single_LL = analyze_malariatherapy_density(analyzers[this_analyzer], site, data[this_analyzer])
        elif this_analyzer == 'malariatherapy_duration_analyzer' :
            single_LL = analyze_malariatherapy_duration(analyzers[this_analyzer], site, data[this_analyzer])
        elif this_analyzer == 'seasonal_infectiousness_analyzer' :
            with open(settings['curr_iteration_dir'] + 'params_withpaths.json') as fin :
                samples = json.loads(fin.read())
            single_LL = analyze_seasonal_infectiousness(analyzers[this_analyzer], site, data[this_analyzer], samples)
        if 'weight_by_site' in settings and site in settings['weight_by_site'] and this_analyzer in settings['weight_by_site'][site] :
            for i in range(numsamples) :
                LL[i] += single_LL[i]*settings['weight_by_site'][site][this_analyzer]
        else :
            for i in range(numsamples) :
                LL[i] += single_LL[i]

    return LL



