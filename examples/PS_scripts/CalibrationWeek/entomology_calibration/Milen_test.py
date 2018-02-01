import random
import json

import calibtool.algorithms.algorithms_PBnB.m_intial_paramters_setting as par
# from MunumbweCalibSite import MunumbweCalibSite
from ClusterCalibSite import ClusterCalibSite
from calibtool.CalibManager import CalibManager
from calibtool.algorithms.algorithms_PBnB.OptimTool_PBnB import OptimTool_PBnB
from calibtool.plotters.OptimToolPBnBPlotter import OptimToolPBnBPlotter
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from simtools.SetupParser import SetupParser
from dtk.vector.species import set_larval_habitat

SetupParser.default_block = 'HPC'

cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')

# Configure the exe
cb.set_experiment_executable('DTK_bins/Eradication.exe')
cb.set_dll_root('DTK_bins')

sites = [ClusterCalibSite()]
plotters = [OptimToolPBnBPlotter()]  # OTP must be last because it calls gc.collect()

with open("cluster_params.json", "r") as cp_f:
    cluster_params = json.load(cp_f)

cluster_id = cluster_params.keys()[0]

bbox_min_x = 0.1
bbox_max_x = 60

bbox_min_y = 0.1
bbox_max_y = 60

if cluster_params[cluster_id]['site'] == 'Sinamalima' or cluster_params[cluster_id]['site'] == 'Munumbwe':
    bbox_min_x = 0.1
    bbox_max_x = 75
    bbox_min_y = 0.1
    bbox_max_y = 150

if cluster_params[cluster_id]['site'] == 'Lukonde' or cluster_params[cluster_id]['site'] == 'Gwembe':
    bbox_min_x = 0.1
    bbox_max_x = 50
    bbox_min_y = 0.1
    bbox_max_y = 50

calib_name = cluster_params.keys()[0]

params = [
    {
        'Name': 'funestus_scale',
        'Dynamic': True,
        'MapTo': 'funestus_scale',  # <-- DEMO: Custom mapping, see map_sample_to_model_input below
        'Guess': 5,
        'Min': bbox_min_x,
        'Max': bbox_max_x
    },
    {
        'Name': 'arabiensis_scale',
        'Dynamic': True,
        'MapTo': 'arabiensis_scale',
        'Guess': 5,
        'Min': bbox_min_y,
        'Max': bbox_max_y
    },
]


def map_sample_to_model_input(cb, sample):
    tags = {}

    if 'arabiensis_scale' in sample:
        a_sc = sample.pop('arabiensis_scale')

        hab = {'arabiensis': {'TEMPORARY_RAINFALL': 1e8 * a_sc, 'CONSTANT': 2e6}}
        set_larval_habitat(cb, hab)

        tags.update({'arabiensis_scale': a_sc})

    if 'funestus_scale' in sample:
        f_sc = sample.pop('funestus_scale')

        hab = {'funestus': {
            "WATER_VEGETATION": 2e7,
            "LINEAR_SPLINE": {
                "Capacity_Distribution_Per_Year": {
                    "Times": [0.0, 30.417, 60.833, 91.25, 121.667, 152.083, 182.5, 212.917, 243.333, 273.75, 304.167,
                              334.583],
                    "Values": [0.0, 0.0, 0.0, 0.0, 0.2, 1.0, 1.0, 1.0, 0.5, 0.2, 0.0, 0.0]
                },
                "Max_Larval_Capacity": 1e8 * f_sc
            }
        }
        }

        set_larval_habitat(cb, hab)

        tags.update({'funestus_scale': f_sc})

    for name, value in sample.iteritems():
        print
        'UNUSED PARAMETER:', name
    assert (len(sample) == 0)  # All params used

    # Run for 10 years with a random random number seed
    cb.set_param('Simulation_Duration', 3650)  # 10*365
    cb.set_param('Vector_Species_Names', ["arabiensis", "funestus"])
    tags.update(cb.set_param('Run_Number', random.randint(0, 1e6)))

    return tags

    '''
    # Can perform custom mapping, e.g. a trivial example
    if 'Clinical Fever Threshold High' in sample:
        value = sample.pop('Clinical Fever Threshold High')
        tags.update( cb.set_param('Clinical_Fever_Threshold_High', value) )

    for p in params:
        if 'MapTo' in p:
            if p['Name'] not in sample:
                print 'Warning: %s not in sample, perhaps resuming previous iteration' % p['Name']
                continue
            value = sample.pop( p['Name'] )
            tags.update( cb.set_param(p['Name'], value) )

    for name,value in sample.iteritems():
        print 'UNUSED PARAMETER:', name
    assert( len(sample) == 0 ) # All params used

    # Run for 10 years with a random random number seed
    tags.update(cb.set_param('Simulation_Duration', 3650))      # 10*365
    tags.update(cb.set_param('Run_Number', random.randint(0, 1e6)))

    return tags
    '''


optimtool_PBnB = OptimTool_PBnB(params,
                                s_running_file_name=calib_name + '_Optimization_PBnB',
                                s_problem_type='deterministic',  # deterministic or noise
                                f_delta=par.f_delta,  # <-- to determine the quantile for the target level set
                                f_alpha=par.f_alpha,  # <-- to determine the quality of the level set approximation
                                i_k_b=par.i_k_b,  # <-- maximum number of inner iterations
                                i_n_branching=par.i_n_branching,  # <-- number of branching subregions
                                i_c=par.i_c,  # <--  increaing number of sampling points ofr all
                                i_replication=par.i_replication,  # <-- initial number of replication
                                i_stopping_max_k=par.i_stopping_max_k,  # <-- maximum number of outer iterations
                                i_num_simulation_per_run=par.i_num_simulation_per_run,
                                )  # <-- maximum number of simulations per iter

calib_manager = CalibManager(name=calib_name + '_Optimization_PBnB',  # <-- Please customize this name
                             config_builder=cb,
                             map_sample_to_model_input_fn=map_sample_to_model_input,
                             sites=sites,
                             next_point=optimtool_PBnB,
                             sim_runs_per_param_set=1,  # <-- Replicates
                             max_iterations=30,  # <-- Iterations
                             plotters=plotters)
run_calib_args = {}

if __name__ == "__main__":
    SetupParser.init()
    calib_manager.run_calibration()