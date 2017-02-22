from calibtool.CalibManager import CalibManager
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from examples.example_iterative.GenericIterativeNextPoint import GenericIterativeNextPoint
from examples.example_iterative.MyanmarSite import MyanmarCalibSite
from simtools.SetupParser import SetupParser

cb = DTKConfigBuilder.from_files(config_name='config.json', campaign_name='campaign.json')
cb.set_param('Simulation_Duration', 730)

sites = [
    MyanmarCalibSite()
]

def sample_point_fn(cb, sample_dimension_values):
    print sample_dimension_values
    return {}

calib_manager = CalibManager(name='FullCalibrationExample',
                             setup=SetupParser('HPC'),
                             config_builder=cb,
                             map_sample_to_model_input_fn=sample_point_fn,
                             sites=sites,
                             next_point=GenericIterativeNextPoint(),
                             sim_runs_per_param_set=1,
                             max_iterations=2,
                             plotters=[])


if __name__ == "__main__":
    calib_manager.cleanup()
    calib_manager.run_calibration()