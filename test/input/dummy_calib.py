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
    Antigen_Switch_Rate_LOG=('linear', -10, -8),
)

plotters = [LikelihoodPlotter(True), SiteDataPlotter(True)]

def sample_point_fn(cb, sample_dimension_values):
    '''
    A simple example function that takes a list of sample-point values
    and sets parameters accordingly using the parameter names from the prior.
    Note that more complicated logic, e.g. setting campaign event coverage or habitat abundance by species,
    can be encoded in a similar fashion using custom functions rather than the generic "set_param".
    '''
    sample_point = prior.to_dict(sample_dimension_values)
    params_to_update = dict()
    params_to_update['Simulation_Duration'] = 365
    for sample_dimension_name, sample_dimension_value in sample_point.items():
        param_name = sample_dimension_name.replace('_LOG', '')
        params_to_update[param_name] = pow(10, sample_dimension_value)

    return cb.update_params(params_to_update)


next_point_kwargs = dict(initial_samples=3,
                         samples_per_iteration=3,
                         n_resamples=100)

calib_manager = CalibManager(name='test_dummy_calibration',
                             setup=SetupParser(),
                             config_builder=cb,
                             map_sample_to_model_input_fn=sample_point_fn,
                             sites=sites,
                             next_point=IMIS(prior, **next_point_kwargs),
                             sim_runs_per_param_set=1,
                             max_iterations=2,
                             plotters=plotters)

run_calib_args = {}

if __name__ == "__main__":
    calib_manager.run_calibration(**run_calib_args)
