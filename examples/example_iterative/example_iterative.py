from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from examples.example_iterative.MyanmarSite import MyanmarCalibSite
from simtools.OutputParser import CompsDTKOutputParser
from simtools.SetupParser import SetupParser

from calibtool.CalibManager import CalibManager
from examples.example_iterative.GenericIterativeNextPoint import GenericIterativeNextPoint
from simtools.Utilities.Experiments import retrieve_experiment
import pandas as pd
import os

from dtk.interventions.malaria_drug_campaigns import add_drug_campaign


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

CompsDTKOutputParser.sim_dir_map = None
#cb.update_params({'Num_Cores': 1})

sweep_params = [{'LINEAR_SPLINE': df['minimus.LINEAR_SPLINE'][x]} for x in df.index]


sites = [
    MyanmarCalibSite()
]

# Here we are specifying the initial values for the next point data
initial_state = [{
    'NodeIds':[],
    'Serialization':30,
    'Prevalence_date':365-1,
    'Prevalence_threshold':.1
    # for first iteration, set serialization path and filenames to burn-in
    # should analyzer return path to previous segment?
    #'Serialized_Population_Path':'', #os.path.join(cb_dir, 'output'),
    #'Serialized_Population_Filenames':[]#['state-18250-%03d.dtk' % x for x in range(24)]
}]


def sample_point_fn(cb, sample_dimension_values):
    print len(sample_dimension_values['NodeIds'])

    # also need to pick up serialization path to load serialized file for each iteration.
    if sample_dimension_values['NodeIds'] :
        add_drug_campaign(cb, 'MDA', 'DP', [sample_dimension_values['Serialization']],
                          coverage=0.7, nodes=sample_dimension_values['NodeIds'])
        
    if 'Serialized_Population_Path' in sample_dimension_values:
        cb.set_param('Serialized_Population_Path',sample_dimension_values['Serialized_Population_Path'])
        
    if 'Serialized_Population_Filenames' in sample_dimension_values:
        cb.set_param('Serialized_Population_Filenames',sample_dimension_values['Serialized_Population_Filenames'])

    # to speed up simulations: no vectors, no people
    # require multinode to read in burn-in
    cb.update_params({'x_Temporary_Larval_Habitat':0,
                      'Base_Population_Scale_Factor' : 0.01,
                      'Enable_Vital_Dynamics' : 0,
                      'Simulation_Duration':365,
                      'Spatial_Output_Channels': ['New_Diagnostic_Prevalence'],
                      'New_Diagnostic_Sensitivity': 1,
                      'Serialization_Time_Steps': [sample_dimension_values['Serialization']]
                      })

    return {'Prevalence_date':sample_dimension_values['Prevalence_date'],
            'Prevalence_threshold': sample_dimension_values['Prevalence_threshold'],
            'Serialization':sample_dimension_values['Serialization']}

# sp.override_block('LOCAL')
calib_manager = CalibManager(name='IterativeTest',
                             setup=sp,
                             config_builder=cb,
                             map_sample_to_model_input_fn=sample_point_fn,
                             sites=sites,
                             next_point=GenericIterativeNextPoint(initial_state),
                             sim_runs_per_param_set=1,
                             max_iterations=2,
                             plotters=[])

run_calib_args = {}

if __name__ == "__main__":
    calib_manager.cleanup()
    calib_manager.run_calibration(**run_calib_args)
