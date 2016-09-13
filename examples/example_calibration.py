# Execute directly: 'python example_calibration.py'
# or via the calibtool.py script: 'calibtool run example_calibration.py'

from scipy.stats import uniform

from calibtool.CalibManager import CalibManager
from calibtool.Prior import MultiVariatePrior
from calibtool.algo.IMIS import IMIS
from calibtool.analyzers.DTKCalibFactory import DTKCalibFactory
from calibtool.plotters.LikelihoodPlotter import LikelihoodPlotter
from calibtool.plotters.SiteDataPlotter import SiteDataPlotter

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from simtools.SetupParser import SetupParser

cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')

analyzer = DTKCalibFactory.get_analyzer(
    'ClinicalIncidenceByAgeCohortAnalyzer', weight=1)

sites = [DTKCalibFactory.get_site('Dielmo', analyzers=[analyzer]),
         DTKCalibFactory.get_site('Ndiop', analyzers=[analyzer])]

cb.add_input_file('test.q',"test")

prior = MultiVariatePrior.by_param(
    Transmission_Rate=uniform(loc=0, scale=1),  # from 0 to 1
    MSP1_Merozoite_Kill_Fraction=uniform(loc=0.4, scale=0.3),  # from 0.4 to 0.7
    Nonspecific_Antigenicity_Factor=uniform(loc=0.1, scale=0.8))  # from 0.1 to 0.9

plotters = [LikelihoodPlotter(True), SiteDataPlotter(True)]

def sample_point_fn(cb, param_values):
    """
    A simple example function that takes a list of sample-point values
    and sets parameters accordingly using the parameter names from the prior.
    Note that more complicated logic, e.g. setting campaign event coverage or habitat abundance by species,
    can be encoded in a similar fashion using custom functions rather than the generic "set_param".
    """
    cb.input_files['test.q'] +=  str(param_values[0])

    params_dict = dict(zip(prior.params, param_values))
    for param, value in params_dict.iteritems():
        if param == "Transmission_Rate":
            continue
        cb.set_param(param,value)
    cb.set_param('Simulation_Duration',365)
    return params_dict


next_point_kwargs = dict(initial_samples=4,
                         samples_per_iteration=4,
                         n_resamples=100)

calib_manager = CalibManager(name='ExampleCalibration',
                             setup=SetupParser(),
                             config_builder=cb,
                             sample_point_fn=sample_point_fn,
                             sites=sites,
                             next_point=IMIS(prior, **next_point_kwargs),
                             sim_runs_per_param_set=2,
                             max_iterations=2,
                             num_to_plot=5,
                             plotters=plotters)

run_calib_args = {'selected_block': "EXAMPLE"}

if __name__ == "__main__":
    run_calib_args.update(dict(location='LOCAL'))
    calib_manager.run_calibration(**run_calib_args)
