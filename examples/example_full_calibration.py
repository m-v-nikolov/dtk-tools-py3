# Execute directly: 'python example_calibration.py'
# or via the calibtool.py script: 'calibtool run example_full_calibration.py --hpc'

from simtools.SetupParser import SetupParser

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder

from calibtool.CalibManager import CalibManager
from calibtool.Prior import MultiVariatePrior
from calibtool.algo.IMIS import IMIS
from calibtool.plotters.LikelihoodPlotter import LikelihoodPlotter
from calibtool.plotters.SiteDataPlotter import SiteDataPlotter

from calibtool.study_sites import \
    NdiopCalibSite, DielmoCalibSite, \
    NamawalaCalibSite, RafinMarkeCalibSite, MatsariCalibSite, SugungumCalibSite, \
    LayeCalibSite, DapelogoCalibSite

cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')

sites = [
    RafinMarkeCalibSite(),
    # MatsariCalibSite(),
    # SugungumCalibSite(),
    # NamawalaCalibSite(),
    NdiopCalibSite(),
    # DielmoCalibSite(),
    LayeCalibSite(),
    # DapelogoCalibSite()
]

prior = MultiVariatePrior.by_range(
    Antigen_Switch_Rate=('log', 1e-10, 1e-8),
    # Base_Gametocyte_Production_Rate=('log', 0.001, 0.5),
    Falciparum_MSP_Variants=('linear_int', 5, 50),
    Falciparum_Nonspecific_Types=('linear_int', 5, 100),
    Falciparum_PfEMP1_Variants=('linear_int', 900, 1700),
    # Gametocyte_Stage_Survival_Rate=('linear', 0.5, 0.95),
    MSP1_Merozoite_Kill_Fraction=('linear', 0.4, 0.7),
    # Max_Individual_Infections=('linear_int', 3, 8),
    Nonspecific_Antigenicity_Factor=('linear', 0.1, 0.9)
)

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
    params_dict['Simulation_Duration'] = 365 * 3  # shorter for quick test
    return cb.update_params(params_dict)


next_point_kwargs = dict(initial_samples=20,
                         samples_per_iteration=10,
                         n_resamples=100)

calib_manager = CalibManager(name='FullCalibrationExample',
                             setup=SetupParser(),
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
    calib_manager.cleanup()
    calib_manager.run_calibration(**run_calib_args)
