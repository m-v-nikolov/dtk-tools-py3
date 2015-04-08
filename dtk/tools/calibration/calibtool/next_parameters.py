#####################################################################
# next_parameters.py
#
# A set of functions for generating parameter samples for the next iteration.
#
# update_params() 
# ---
# args: calibration settings, iteration number, previous parameter samples with likelihoods, updater to use
# return: whether to continue calibration
# 
# update_IMIS() 
# --- 
# Requires SciPy version 0.14.1
# Chooses next samples using IMIS and assumes a box prior.
# Saves IMIS state after each iteration. Returns False if IMIS stopping conditions are met.
#
# update_dumb() 
# --- 
# Chooses next samples with a dummy algorithm. Use only for testing.
#
#####################################################################

from utils import update_settings, write_to_file
import numpy as np
import json
import sys
import math
from load_parameters import load_initial_samples_LHC

def update_params(settings, iteration, samples, updater='dumb') :

    keep_going = True
    if iteration == settings['max_iterations'] :
        keep_going = False
    else :
        try :
            fin = open(settings['curr_iteration_dir'] + 'params' + '.json')

        except IOError :
            if updater == 'IMIS' :
                newsamples, keep_going = update_IMIS(settings, iteration, samples)
            elif updater == 'dumb' :
                newsamples, keep_going = update_dumb(settings, samples)
            else :
                print 'updater', updater, 'does not exist.'
                keep_going = False

            if keep_going :
                write_to_file(clean_new_samples(settings, newsamples), settings['curr_iteration_dir'] + 'params')
 
    return keep_going

def update_IMIS(settings, iteration, samples) :

    with open(settings['initial_sampling_range_file']) as fin :
        samplerange = json.loads(fin.read())
    paramnames = samplerange.keys()

    nparrays = ['gaussian_probs', 'samples', 'latest_samples']
    list_of_nparrays = ['gaussian_centers', 'gaussian_covariances']

    curr_status = {}
    isamples = []
    if iteration > 0 :
        with open(settings['prev_iteration_dir'] + 'imis.json') as fin :
            curr_status = json.loads(fin.read())
        for key in curr_status :
            if key in nparrays :
                curr_status[key] = np.array(curr_status[key])
            elif key in list_of_nparrays :
                for i in range(len(curr_status[key])) :
                    curr_status[key][i] = np.array(curr_status[key][i])
    else :
        initial_samples = load_initial_samples_LHC(settings['initial_sampling_range_file'], settings['num_initial_samples'], settings['curr_iteration_dir'])
        isamples = np.zeros((settings['num_initial_samples'], len(paramnames)))
        for j in range(settings['num_initial_samples']) :
            for i in range(len(paramnames)) :
                if 'log' in samplerange[paramnames[i]]['type'] :
                    isamples[j][i] = math.log10(initial_samples[paramnames[i]][j])
                else :
                    isamples[j][i] = initial_samples[paramnames[i]][j]

    logsamplerange = samplerange
    for key in samplerange :
        if 'log' in samplerange[key]['type']  :
            logsamplerange[key]['max'] = math.log10(logsamplerange[key]['max'])
            logsamplerange[key]['min'] = math.log10(logsamplerange[key]['min'])

    IMIS_settings = { 'prior_fn' : box_prior_generator(logsamplerange, paramnames),
                      'n_initial_samples' : settings['num_initial_samples'], 
                      'n_samples_per_iteration' : settings['num_samples_per_iteration'], 
                      'n_iterations' : settings['max_iterations'], 
                      'n_resamples': settings['num_resamples'] }

    sys.path.append(settings['dtk_path'])
    from dtk.tools.calibration.IMIS import IMIS
    
    imis = IMIS.from_iteration_num(iteration, IMIS_settings, curr_status, isamples)

    if iteration > 0 :
        latest_likelihoods = [math.exp(i) for i in samples['LL']]
        imis.set_likelihoods(latest_likelihoods)
        finished = imis.update(iteration-1)
    else :
        finished = False
    
    t = imis.get_current_state()
    for key in t :
        if isinstance(t[key], np.ndarray) :
            t[key] = t[key].tolist()
        elif key in list_of_nparrays and t[key] != [] :
            for i in range(len(t[key])) :
                t[key][i] = t[key][i].tolist()

    write_to_file(t, settings['curr_iteration_dir'] + 'imis', ['json'])
    next_samples = imis.get_next_samples()
    new_samples = {}
    for i in range(len(next_samples[0])) :
        new_samples[paramnames[i]] = [0]*len(next_samples)
        for j in range(len(next_samples)) :
            if 'log' in samplerange[paramnames[i]]['type'] :
                new_samples[paramnames[i]][j] = 10**(next_samples[j][i])
            else :
                new_samples[paramnames[i]][j] = next_samples[j][i]

    return new_samples, not finished

def box_prior_generator(p, paramnames) :
        
    from random import uniform
    class prior_fn :
        def __init__(self, param_limits, paramnames) :
            self.param_limits = param_limits
            self.paramnames = paramnames

        def pdf(self, points) :
            if isinstance(points[0], float) or isinstance(points[0], int) : # if 1-dimensional
                points = [[x] for x in points] 
            t = [all([(point[i] >= self.param_limits[k]['min']) * (point[i] <= self.param_limits[k]['max']) for i, k in enumerate(self.paramnames)]) for point in points]
            return [int(x) for x in t]

        def rvs(self) :
            return [uniform(self.param_limits[k]['min'], self.param_limits[k]['max']) for k in self.param_limits]

    return prior_fn(p, paramnames)

def update_dumb(settings, samples) :

    LL = samples['LL']
    del samples['LL']

    from operator import itemgetter

    num_top = min([max([10, settings['num_resamples']]), len(LL)])
    d = sorted([(item, i) for i, item in enumerate(LL)], key=itemgetter(0), reverse=True)
    top_LL_index = [x[1] for x in d][:num_top]

    newsamples = {}

    for par in samples :
        parval = [samples[par][i] for i in top_LL_index]        
        t = np.linspace(min(parval), max(parval), settings['num_samples_per_iteration'])
        np.random.shuffle(t)
        newsamples[par] = t.tolist()
    
    return newsamples, True

def clean_new_samples(settings, samples) :

    with open(settings['initial_sampling_range_file']) as fin :
        samplerange = json.loads(fin.read())

    for par in samplerange :        
        if 'int' in samplerange[par]['type'] :
            samples[par] = [int(x) for x in samples[par]]

    return samples
