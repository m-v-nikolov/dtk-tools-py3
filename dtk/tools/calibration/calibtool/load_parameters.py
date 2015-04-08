#####################################################################
# load_parameters.py
#
# A set of functions for loading parameters into a dictionary and
# constructing initial samples.
#
# load_samples() 
# ---
# args: calibration settings and iteration number
# return: parameter values as dictionary
# Looks for params.json in current working directory. If not found and
# on first iteration, calls fxn to calculate initial samples. Returns
# dictionary as {param_name : [values]}
# 
# load_initial_samples_LHC() 
# --- 
# args: filename containing info for initial samples, number of
# initial samples, current working directory
# return : parameter values as dictionary
# Loads json file containing info for initial sampling: parameter
# names, upper and lower bounds, log or linear sampling, whether must
# be int. Returns LHC sampling as a dictionary {param_name :
# [values]}.
#
#####################################################################

import numpy as np
from math import log10
import json
from utils import write_to_file

def load_samples(settings, iteration) :

    parameter_dir = settings['curr_iteration_dir']
    fname = parameter_dir + 'params'

    try :
        with open(fname + '.json') as fin :
            samples = json.loads(fin.read())

    except IOError :
        samples = {}
        if iteration == 0 :
            num_initial_samples = settings['num_initial_samples']
            initial_sampling_type = settings['initial_sampling_type']
            initial_sampling_range_file = settings['initial_sampling_range_file']
            if initial_sampling_type == 'LHC' :
                samples = load_initial_samples_LHC(initial_sampling_range_file, num_initial_samples, parameter_dir)

        write_to_file(samples, fname)

    return samples

def load_initial_samples_LHC(initial_sampling_range_file, num_initial_samples, parameter_dir) :

    with open(initial_sampling_range_file) as fin :
        samplerange = json.loads(fin.read())

    samples = {}
    for param in samplerange.keys() :
        if 'log' in samplerange[param]['type'] :
            samples[param] = np.logspace(log10(samplerange[param]['min']),
                                         log10(samplerange[param]['max']),
                                         num_initial_samples)
        else :
            samples[param] = np.linspace(samplerange[param]['min'],
                                         samplerange[param]['max'],
                                         num_initial_samples)

        np.random.shuffle(samples[param])
        if 'int' in samplerange[param]['type'] :
            samples[param] = [int(x) for x in samples[param].tolist()]
        else :
            samples[param] = samples[param].tolist()
    
    return samples
