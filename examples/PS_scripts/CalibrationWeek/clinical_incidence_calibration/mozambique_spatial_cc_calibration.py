# Execute directly: 'python example_optimization.py'
# or via the calibtool.py script: 'calibtool run example_optimization.py'
import copy
import math
import random
import numpy as np

from scipy.special import gammaln

from calibtool.CalibManager import CalibManager
from calibtool.algorithms.OptimTool import OptimTool
from calibtool.plotters.LikelihoodPlotter import LikelihoodPlotter
from calibtool.plotters.OptimToolPlotter import OptimToolPlotter
from calibtool.plotters.SiteDataPlotter import SiteDataPlotter
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.vector.species import set_larval_habitat
from simtools.SetupParser import SetupParser

try:
    from malaria.study_sites.MoineSpatialCalibSite import MoineSpatialCalibSite
except ImportError as e:
    message = "The malaria package needs to be installed before running this example...\n" \
                "Please run `dtk get_package malaria -v HEAD` to install"
    raise ImportError(message)

# Which simtools.ini block to use for this calibration
SetupParser.default_block = 'HPC'

# Start from a base MALARIA_SIM config builder
# This config builder will be modify by the different sites defined below
cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')
# cb.set_collection_id('a7f64605-2a05-e811-9415-f0921c16b9e5') # COMPS


# List of sites we want to calibrate on
specs = ['funestus', 'gambiae']
sites = [MoineSpatialCalibSite()]

# The default plotters used in an Optimization with OptimTool
plotters = [LikelihoodPlotter(combine_sites=True),
            #SiteDataPlotter(num_to_plot=5, combine_sites=True),
            OptimToolPlotter()  # OTP must be last because it calls gc.collect()
]


bbox_min_funestus_wet = 0.01
bbox_max_funestus_wet = 20

bbox_min_funestus_dry = 0.01
bbox_max_funestus_dry = 10

bbox_min_gambiae_wet = 0.01
bbox_max_gambiae_wet = 20

bbox_min_gambiae_dry = 0.01
bbox_max_gambiae_dry = 10


params = [
    {
        'Name': 'funestus_scale_dry',
        'Dynamic': True,
        'MapTo': 'funestus_scale_dry',  # <-- DEMO: Custom mapping, see map_sample_to_model_input below
        'Guess': 0.5,
        'Min': bbox_min_funestus_dry,
        'Max': bbox_max_funestus_dry
    },
    {
        'Name': 'funestus_scale_wet',
        'Dynamic': True,
        'MapTo': 'funestus_scale_wet',  # <-- DEMO: Custom mapping, see map_sample_to_model_input below
        'Guess': 0.5,
        'Min': bbox_min_funestus_wet,
        'Max': bbox_max_funestus_wet
    },
    {
        'Name': 'gambiae_scale_dry',
        'Dynamic': True,
        'MapTo': 'gambiae_scale_dry',  # <-- DEMO: Custom mapping, see map_sample_to_model_input below
        'Guess': 0.5,
        'Min': bbox_min_gambiae_dry,
        'Max': bbox_max_gambiae_dry
    },
    {
        'Name': 'gambiae_scale_wet',
        'Dynamic': True,
        'MapTo': 'gambiae_scale_wet',  # <-- DEMO: Custom mapping, see map_sample_to_model_input below
        'Guess': 0.5,
        'Min': bbox_min_gambiae_wet,
        'Max': bbox_max_gambiae_wet
    }

]


# TSI-based profile for Moine (may want to have separate profiles for different species in the future)
wet_profile = {
    0: 0.8,
    1: 0.85,
    2: 0.7,
    3: 0.6,
    8: 0.55,
    9: 0.7,
    10: 0.75,
    11: 0.8
}

dry_profile = {
    4: 0.35,
    5: 0.1,
    6: 0.02,
    7: 0.15
}


def map_sample_to_model_input(cb, sample):
    tags = {}

    if 'gambiae_scale_dry' in sample and 'gambiae_scale_wet' in sample:
        g_sc_dry = sample.pop('gambiae_scale_dry')
        g_sc_wet = sample.pop('gambiae_scale_wet')

        seasonal_TSI = np.zeros(12)
        seasonal_TSI[np.array(list(wet_profile.keys()))] = g_sc_wet * np.array(list(wet_profile.values()))
        seasonal_TSI[np.array(list(dry_profile.keys()))] = g_sc_dry * np.array(list(dry_profile.values()))

        hab = {'gambiae': {'CONSTANT': 2e6,
                           "LINEAR_SPLINE": {
                               "Capacity_Distribution_Per_Year": {
                                   "Times": [0.0, 30.417, 60.833, 91.25, 121.667, 152.083, 182.5, 212.917, 243.333, 273.75, 304.167, 334.583],
                                   "Values": list(seasonal_TSI)
                               },
                               "Max_Larval_Capacity": 1e8
                }
            }
        }
        set_larval_habitat(cb, hab)

        tags.update({'gambiae_scale_dry': g_sc_dry, 'gambiae_scale_wet': g_sc_wet})


    if 'funestus_scale_dry' in sample and 'funestus_scale_wet' in sample:

        f_sc_dry = sample.pop('funestus_scale_dry')
        f_sc_wet = sample.pop('funestus_scale_wet')

        seasonal_TSI = np.zeros(12)

        seasonal_TSI[np.array(list(wet_profile.keys()))] = f_sc_wet * np.array(list(wet_profile.values()))
        seasonal_TSI[np.array(list(dry_profile.keys()))] = f_sc_dry * np.array(list(dry_profile.values()))

        hab = {'funestus': {
            "WATER_VEGETATION": 2e7,
            "LINEAR_SPLINE": {
                "Capacity_Distribution_Per_Year": {
                    "Times": [0.0, 30.417, 60.833, 91.25, 121.667, 152.083, 182.5, 212.917, 243.333, 273.75, 304.167, 334.583],
                    "Values": list(seasonal_TSI)
                },
                "Max_Larval_Capacity": 1e8
            }
        }
        }



        set_larval_habitat(cb, hab)

        tags.update({'funestus_scale_dry': f_sc_dry, 'funestus_scale_wet': f_sc_wet})

    for name, value in sample.items():
        print('UNUSED PARAMETER:', name)
    assert (len(sample) == 0)  # All params used

    return tags



# Just for fun, let the numerical derivative baseline scale with the number of dimensions
volume_fraction = 0.05   # desired fraction of N-sphere area to unit cube area for numerical derivative (automatic radius scaling with N)
num_params = len([p for p in params if p['Dynamic']])
r = math.exp(1/float(num_params)*(math.log(volume_fraction) + gammaln(num_params/2.+1) - num_params/2.*math.log(math.pi)))

optimtool = OptimTool(params,
    mu_r = r,           # <-- radius for numerical derivatve.  CAREFUL not to go too small with integer parameters
    sigma_r = r/10.,    # <-- stdev of radius
    center_repeats = 1, # <-- Number of times to replicate the center (current guess).  Nice to compare intrinsic to extrinsic noise
    samples_per_iteration = 18  # 32 # <-- Samples per iteration, includes center repeats.  Actual number of sims run is this number times number of sites.
)


# cb.add_reports(BaseVectorStatsReport(type='ReportVectorStats', stratify_by_species=1))

calib_manager = CalibManager(name='MoineIncidenceSpatialCalibIterTest',    # <-- Please customize this name
                             config_builder=cb,
                             map_sample_to_model_input_fn=map_sample_to_model_input,
                             sites=sites,
                             next_point=optimtool,
                             sim_runs_per_param_set=1,  # <-- Replicates
                             max_iterations=20,          # <-- Iterations
                             plotters=plotters)


run_calib_args = {
    "calib_manager":calib_manager
}

if __name__ == "__main__":
    SetupParser.init()
    cm = run_calib_args["calib_manager"]
    cm.run_calibration()
