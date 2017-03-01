from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from examples.example_iterative.MyanmarSite import MyanmarCalibSite
from simtools.SetupParser import SetupParser

from calibtool.CalibManager import CalibManager
from examples.example_iterative.GenericIterativeNextPoint import GenericIterativeNextPoint
from simtools.Utilities.Experiments import retrieve_experiment
import pandas as pd
import os


# Find experiment from whose config/campaigns we want to use (also get sweep params)
comparison_exp_id = "9e042fad-27fb-e611-9400-f0921c16849c"
expt = retrieve_experiment(comparison_exp_id)
sp = SetupParser('HPC')

df = pd.DataFrame([x.tags for x in expt.simulations])
df['outpath'] = pd.Series([sim.get_path() for sim in expt.simulations])

# generate cb object from the first of these files (the only difference will be in the sweep params)
cb_dir = df['outpath'][0]
cb = DTKConfigBuilder.from_files(config_name=os.path.join(cb_dir, 'config.json'),
                                 campaign_name=os.path.join(cb_dir, 'campaign.json'))

sweep_params = [{'LINEAR_SPLINE': df['minimus.LINEAR_SPLINE'][x]} for x in df.index]


sites = [
    MyanmarCalibSite()
]

initial_values = {
    'x_Temporary_Larval_Habitat':[1,2,3],
    'Run_Nunber':[4,5,6]
}


def sample_point_fn(cb, sample_dimension_values):
    print sample_dimension_values
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
