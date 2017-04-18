# Execute directly: 'python example_optimization.py'
# or via the calibtool.py script: 'calibtool run example_optimization.py'
import math

from scipy.special import gammaln

from calibtool.CalibManager import CalibManager
from calibtool.algo.OptimTool import OptimTool
from calibtool.plotters.LikelihoodPlotter import LikelihoodPlotter
from calibtool.plotters.OptimToolPlotter import OptimToolPlotter
from calibtool.study_sites.DielmoCalibSite import DielmoCalibSite
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from simtools.SetupParser import SetupParser

cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')

sites = [DielmoCalibSite()]

plotters = [LikelihoodPlotter(combine_sites=True),
            OptimToolPlotter()
]

params = [
    {
        'Name': 'Clinical Fever Threshold High',
        'Dynamic': True,
        'Guess': 1.75,
        'Min': 0.5,
        'Max': 2.5
    },
    {
        'Name': 'MSP1 Merozoite Kill Fraction',
        'Dynamic': False,   # <-- NOTE: this parameter is frozen at Guess
        'MapTo': 'MSP1_Merozoite_Kill_Fraction',
        'Guess': 0.65,
        'Min': 0.4,
        'Max': 0.7
    }
]

def map_sample_to_model_input(cb, sample):
    return cb.update_params(sample)

# Let the numerical derivative baseline scale with the number of dimensions
# desired fraction of N-sphere area to unit cube area for numerical derivative (automatic radius scaling with N)
volume_fraction = 0.05
num_params = len( [p for p in params if p['Dynamic']] )
r = math.exp( 1/float(num_params)*( math.log(volume_fraction) + gammaln(num_params/2.+1) - num_params/2.*math.log(math.pi) ) )

optimtool = OptimTool(params,
    mu_r = r,           # <-- radius for numerical derivatve.  CAREFUL not to go too small with integer parameters
    sigma_r = r/10.,    # <-- stdev of radius
    center_repeats = 2, # <-- Number of times to replicate the center (current guess).  Nice to compare intrinsic to extrinsic noise
    samples_per_iteration = 4  # 32 # <-- Samples per iteration, includes center repeats.  Actual number of sims run is this number times number of sites.
)

calib_manager = CalibManager(name='ExampleOptimization',    # <-- Name of the experiment
                             setup = SetupParser('HPC'),
                             config_builder = cb,
                             map_sample_to_model_input_fn = map_sample_to_model_input,
                             sites = sites,
                             next_point = optimtool,
                             sim_runs_per_param_set = 1, # <-- Replicates
                             max_iterations = 3,         # <-- Iterations
                             plotters = plotters)

run_calib_args = {}

if __name__ == "__main__":
    calib_manager.run_calibration(**run_calib_args)
