# Template script for analyzing and visualizing simulation output from calibtool
#
# Replace all instances of TEMPLATE with new analyzer name.
# Replace all instances of DATATYPE with data descriptor
#
#

import numpy as np
import LL_calculators
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.ticker import FixedLocator
import pandas as pd
import json
import math
import seaborn as sns
from study_sites.set_calibration_site import get_reference_data

def analyze_prevalence_by_age_noncohort(settings, analyzer, site, data, samples) :

    LL_fn = getattr(LL_calculators, analyzer['LL_fn'])
    raw_data_all = get_reference_data(site, 'prevalence_by_age')
    age_bins = raw_data_all['age_bins']
        
    field = analyzer['fields_to_get'][0]
    raw_data_field = [int(x) for x in fraction_to_number(raw_data_all['n_obs'], raw_data_all[field])]
    n_raw, raw_data = raw_data_all['n_obs'], raw_data_field
    
    LL = [0]*len(samples.index)

    record_data_by_sample = { 'prevalence_by_age' : [] }
    for rownum in range(len(LL)) :

        sim_data = [np.mean([data[y][field][rownum][0][x] for y in range(settings['sim_runs_per_param_set'])]) for x in range(len(age_bins))]
        n_sim = [np.mean([data[y]['Average Population by Age Bin'][rownum][0][x] for y in range(settings['sim_runs_per_param_set'])]) for x in range(len(age_bins))]

        LL[rownum] += LL_fn(n_raw, n_sim, raw_data, sim_data)

        record_data_by_sample['prevalence_by_age'].append(sim_data)

    record_data_by_sample['bins'] = [age_bins[i] for i in range(len(age_bins)) if i not in empty_bins]
    with open(settings['curr_iteration_dir'] + site + '_' + analyzer['name'] + '.json', 'w') as fout :
        json.dump(record_data_by_sample, fout)
    return LL

def visualize_prevalence_by_age_noncohort(settings, iteration, analyzer, site, samples, top_LL_index) :

    from analyze_prevalence_by_age_cohort import visualize_prevalence_by_age_cohort
    visualize_prevalence_by_age_cohort(settings, iteration, analyzer, site, samples, top_LL_index)

def fraction_to_number(n, f) :

    return [f[i]*n[i] for i in range(len(n))]