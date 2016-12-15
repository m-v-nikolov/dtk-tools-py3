# Execute directly: 'python example_calibration.py'
# or via the calibtool.py script: 'calibtool run example_calibration.py'

from calibtool.CalibManager import CalibManager
from calibtool.Prior import MultiVariatePrior
from calibtool.algo.IMIS import IMIS
from calibtool.plotters.LikelihoodPlotter import LikelihoodPlotter
from calibtool.plotters.SiteDataPlotter import SiteDataPlotter
from calibtool.study_sites.DielmoCalibSite import DielmoCalibSite

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from simtools.SetupParser import SetupParser

cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')

sites = [DielmoCalibSite()]

prior = MultiVariatePrior.by_range(
    MSP1_Merozoite_Kill_Fraction=('linear', 0.4, 0.7),
    Max_Individual_Infections=('linear_int', 3, 8),
    Base_Gametocyte_Production_Rate=('log', 0.001, 0.5))

plotters = [
    LikelihoodPlotter(combine_sites=True),
    SiteDataPlotter(combine_sites=True)
]


def sample_point_fn(cb, param_values):
    """
    A simple example function that takes a list of sample-point values
    and sets parameters accordingly using the parameter names from the prior.
    Note that more complicated logic, e.g. setting campaign event coverage or habitat abundance by species,
    can be encoded in a similar fashion using custom functions rather than the generic "set_param".
    """
    params_dict = prior.to_dict(param_values)  # aligns names and values; also rounds integer-range_type params
    params_dict['Simulation_Duration'] = 365  # shorter for quick test
    return cb.update_params(params_dict)


next_point_kwargs = dict(initial_samples=4,
                         samples_per_iteration=4,
                         n_resamples=100)

calib_manager = CalibManager(name='ExampleCalibration',
                             setup=SetupParser(),
                             config_builder=cb,
                             map_sample_to_model_input_fn=sample_point_fn,
                             sites=sites,
                             next_point=IMIS(prior, **next_point_kwargs),
                             sim_runs_per_param_set=2,
                             max_iterations=2,
                             plotters=plotters)

run_calib_args = {}

if __name__ == "__main__":
    run_calib_args.update(dict(location='LOCAL'))
    calib_manager.run_calibration(**run_calib_args)
