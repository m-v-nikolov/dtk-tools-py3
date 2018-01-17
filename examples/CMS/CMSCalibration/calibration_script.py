# Execute directly: 'python example_optimization.py'
# or via the calibtool.py script: 'calibtool run example_optimization.py'
import copy

import re

import numpy as np

from calibtool.CalibManager import CalibManager
from calibtool.algorithms.OptimTool import OptimTool
from calibtool.plotters.LikelihoodPlotter import LikelihoodPlotter
from calibtool.plotters.OptimToolPlotter import OptimToolPlotter
from calibtool.plotters.SiteDataPlotter import SiteDataPlotter
from examples.CMS.CMSCalibration.CMSSIte import CMSSite
from models.cms.core.CMSConfigBuilder import CMSConfigBuilder
from simtools.AssetManager.SimulationAssets import SimulationAssets
from simtools.SetupParser import SetupParser

# Which simtools.ini block to use for this calibration
SetupParser.default_block = 'HPC'

# Start from a base MALARIA_SIM config builder
# This config builder will be modify by the different sites defined below
cb = CMSConfigBuilder.from_files(model_file='base/simplemodel.emodl',
                                 config_file='base/simplemodel.cfg')

try:
    cb.set_collection_id('CMS 0.82 Pre-release')
except SimulationAssets.InvalidCollection:
    cb.set_experiment_executable('../inputs/compartments/compartments.exe')
    cb.set_dll_root('../inputs/compartments')

# List of sites we want to calibrate on
sites = [CMSSite()]

# The default plotters used in an Optimization with OptimTool
plotters = [OptimToolPlotter()]

params = [
    {
        'Name': 'initial_S',
        'Dynamic': True,
        'Guess': 10,
        'Min': 0,
        'Max': 10000
    },
    {
        'Name': 'initial_I',
        'Dynamic': True,
        'Guess': 10,
        'Min': 0,
        'Max': 10000
    }
]


def constrain_sample(sample):
    # Force only integer because all of our parameters should be integers
    # Recast to float64 as the next point algorithm only works with floats
    return sample.astype(np.int).astype(np.float64)


def map_sample_to_model_input(cb, sample):
    tags = {}
    # Make a copy of samples so we can alter it safely
    sample = copy.deepcopy(sample)

    # Go through the parameters
    for p in params:
        value = sample.pop(p['Name'])
        # Replace the (species S 100) with the correct number coming from our sample
        if p["Name"] == "initial_S":
            exp = re.compile(r'\(species S \d+\)', re.I)
            cb.model = exp.sub('(species S {})'.format(int(value)), cb.model)

        # Replaces the (species I 100) with the correct number coming from our sample
        elif p["Name"] == "initial_I":
            exp = re.compile(r'\(species I \d+\)', re.I)
            cb.model = exp.sub('(species I {})'.format(int(value)), cb.model)

        # Add this change to our tags
        tags.update(cb.set_param(p['Name'], value))

    return tags


optimtool = OptimTool(params,
                      constrain_sample,
                      samples_per_iteration=25,
                      center_repeats=1)

calib_manager = CalibManager(name='ExampleOptimizationCMS',
                             config_builder=cb,
                             map_sample_to_model_input_fn=map_sample_to_model_input,
                             sites=sites,
                             next_point=optimtool,
                             sim_runs_per_param_set=1,
                             max_iterations=3,
                             plotters=plotters)

run_calib_args = {
    "calib_manager": calib_manager
}

if __name__ == "__main__":
    SetupParser.init()
    cm = run_calib_args["calib_manager"]
    cm.run_calibration()
