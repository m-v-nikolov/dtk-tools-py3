from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from examples.example_iterative.MyanmarSite import MyanmarCalibSite
from simtools.SetupParser import SetupParser

from calibtool.CalibManager import CalibManager
from examples.example_iterative.GenericIterativeNextPoint import GenericIterativeNextPoint

cb = DTKConfigBuilder.from_files(config_name='config.json', campaign_name='campaign.json')
cb.set_param('Simulation_Duration', 730)

sites = [
    MyanmarCalibSite()
]

initial_values = {
    'x_Temporary_Larval_Habitat':[1,2,3],
    'Run_Nunber':[4,5,6]
}


def sample_point_fn(cb, sample_dimension_values):
    return cb.update_params(sample_dimension_values)

calib_manager = CalibManager(name='FullCalibrationExample',
                             setup=SetupParser(),
                             config_builder=cb,
                             map_sample_to_model_input_fn=sample_point_fn,
                             sites=sites,
                             next_point=GenericIterativeNextPoint(initial_values),
                             sim_runs_per_param_set=1,
                             max_iterations=2,
                             plotters=[])


if __name__ == "__main__":
    calib_manager.cleanup()
    calib_manager.run_calibration()