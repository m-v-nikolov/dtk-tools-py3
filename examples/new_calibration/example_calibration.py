from calibtool.CalibManager import CalibManager
from calibtool.Prior import MultiVariatePrior
from calibtool.algo.IMIS import IMIS
from calibtool.plotters.LikelihoodPlotter import LikelihoodPlotter

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from examples.new_calibration.SiteDataPlotter import SiteDataPlotter
from examples.new_calibration.site_Dielmo import DielmoClibrationSite
from simtools.SetupParser import SetupParser

cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')

sites = [DielmoClibrationSite()]

prior = MultiVariatePrior.by_range(
    MSP1_Merozoite_Kill_Fraction=('linear', 0, 1),
    Max_Individual_Infections=('linear_int', 2, 30)
)

plotters = [
    LikelihoodPlotter(combine_sites=True, prior_fn=prior),
    SiteDataPlotter(combine_sites=True)
]


def sample_point_fn(cb, param_values):
    params_dict = prior.to_dict(param_values)
    cb.set_param('Simulation_Duration', 365)
    return cb.update_params(params_dict)


next_point_kwargs = dict(initial_samples=4,
                         samples_per_iteration=4,
                         n_resamples=100)

calib_manager = CalibManager(name='ExampleCalibration',
                             setup=SetupParser('HPC'),
                             config_builder=cb,
                             sample_point_fn=sample_point_fn,
                             sites=sites,
                             next_point=IMIS(prior, **next_point_kwargs),
                             sim_runs_per_param_set=2,
                             max_iterations=2,
                             num_to_plot=5,
                             plotters=plotters)

run_calib_args = {}

if __name__ == "__main__":
    run_calib_args.update(dict(location='HPC'))
    calib_manager.run_calibration(**run_calib_args)