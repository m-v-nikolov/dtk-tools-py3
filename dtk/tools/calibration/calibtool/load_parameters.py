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
import os

import numpy as np
from math import log10
import json
from utils import write_to_file
import pandas as pd

def load_samples(settings, iteration) :

    parameter_dir = settings['curr_iteration_dir']
    fname = os.path.join(parameter_dir,'params.csv')

    try :
        samples = pd.read_csv(fname)

    except IOError :
        if iteration == 0 :
            num_initial_samples = settings['num_initial_samples']
            initial_sampling_type = settings['initial_sampling_type']
            initial_sampling_range_file = settings['initial_sampling_range_file']
            if initial_sampling_type == 'LHC' :
                samples = load_initial_samples_LHC(initial_sampling_range_file, num_initial_samples, parameter_dir)

        write_to_file(samples, fname)

    return samples

def load_initial_samples_LHC(initial_sampling_range_file, num_initial_samples, parameter_dir) :

    samplerange = pd.read_csv(initial_sampling_range_file)
    samplerange.to_csv(os.path.join(parameter_dir,'initial_sampling_range.csv'))

    samples = {}
    for i in samplerange.index :
        param = samplerange.ix[i, 'parameter']
        if 'log' in samplerange.ix[i, 'type'] :
            samples[param] = np.logspace(log10(samplerange.ix[i, 'min']),
                                         log10(samplerange.ix[i, 'max']),
                                         num_initial_samples)
        else :
            samples[param] = np.linspace(samplerange.ix[i, 'min'],
                                         samplerange.ix[i, 'max'],
                                         num_initial_samples)

        np.random.shuffle(samples[param])
        if 'int' in samplerange.ix[i, 'type'] :
            samples[param] = [int(x) for x in samples[param].tolist()]
        else :
            samples[param] = samples[param].tolist()
    
    return pd.DataFrame(samples)
