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

prior = MultiVariatePrior.by_param(
    MSP1_Merozoite_Kill_Fraction=uniform(loc=0.4, scale=0.3),  # from 0.4 to 0.7
    Nonspecific_Antigenicity_Factor=uniform(loc=0.1, scale=0.8))  # from 0.1 to 0.9

plotters = [LikelihoodPlotter(True), SiteDataPlotter(True)]
# plotters = [LikelihoodPlotter(True)]
# plotters = [SiteDataPlotter(True)]
# plotters = []

def sample_point_fn(cb, param_values):
    '''
    A simple example function that takes a list of sample-point values
    and sets parameters accordingly using the parameter names from the prior.
    Note that more complicated logic, e.g. setting campaign event coverage or habitat abundance by species,
    can be encoded in a similar fashion using custom functions rather than the generic "set_param".
    '''
    params_dict = dict(zip(prior.params, param_values))
    params_dict['Simulation_Duration'] = 365  # shorter for quick test
    return cb.update_params(params_dict)


next_point_kwargs = dict(initial_samples=4,
                         samples_per_iteration=3,
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

run_calib_args = {}

if __name__ == "__main__":
    # run_calib_args.update(dict(location='LOCAL'))
    # calib_manager.run_calibration(**run_calib_args)
    # calib_manager.resume_from_iteration(**run_calib_args)
    calib_manager.replot_calibration(**run_calib_args)
    # setup = SetupParser(selected_block='HPC', force=True)
    # setup = SetupParser(selected_block='HPC', force=True)
    # print setup.get('type')

    # from ConfigParser import ConfigParser
    # setup = ConfigParser()
    # setup.read('C:\\Projects\\dtk-tools-zdu\\simtools\\simtools.ini')
    # print setup.get('HPC', 'type')




    # exit()
