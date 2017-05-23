from calibtool.algorithms.GenericIterativeNextPoint import GenericIterativeNextPoint
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from examples.example_iterative.MyanmarSite import MyanmarCalibSite
from simtools.OutputParser import CompsDTKOutputParser
from simtools.SetupParser import SetupParser

from calibtool.CalibManager import CalibManager
from simtools.Utilities.Experiments import retrieve_experiment
import pandas as pd
import os

from dtk.interventions.malaria_drug_campaigns import add_drug_campaign


SetupParser.init('HPC')

# Find experiment from whose config/campaigns we want to use (also get sweep params)
comparison_exp_id =  "9945ae69-3106-e711-9400-f0921c16849c"
sim_name = 'Rerun_Rampup_MDA_Better_Diagnostic'
expt = retrieve_experiment(comparison_exp_id)


df = pd.DataFrame([x.tags for x in expt.simulations])
df['outpath'] = pd.Series([sim.get_path() for sim in expt.simulations])

# generate cb object from the first of these files (the only difference will be in the sweep params)
cb_dir = df['outpath'][0]

cb = DTKConfigBuilder.from_files(config_name=os.path.join(cb_dir, 'config.json'),
                                 campaign_name=os.path.join(cb_dir, 'campaign.json'))

CompsDTKOutputParser.sim_dir_map = None
#cb.update_params({'Num_Cores': 1})

sites = [
    MyanmarCalibSite()
]

# Here we are specifying the initial values for the next point data
initial_state = [{
    'NodeIDs':[],
    'Serialization':2007,
    'Prevalence_date':2006,
    'Prevalence_threshold':0.4,
    'New_Duration': 1643, # Duration of second iteration
    'Run_Number': rn
    # for first iteration, set serialization path and filenames to burn-in
    # should analyzer return path to previous segment?
    # 'Serialized_Population_Path':'', #os.path.join(cb_dir, 'output'),
    # 'Serialized_Population_Filenames':[]#['state-18250-%03d.dtk' % x for x in range(24)]
} for rn in range(2)]

# initial_state = [{
#     'NodeIDs':[],
#     'Serialization':10,
#     'Prevalence_date':9,
#     'Prevalence_threshold':0.4,
#     'New_Duration': 10, # Duration of second iteration
#     'Run_Number': rn
#     # for first iteration, set serialization path and filenames to burn-in
#     # should analyzer return path to previous segment?
#     # 'Serialized_Population_Path':'', #os.path.join(cb_dir, 'output'),
#     # 'Serialized_Population_Filenames':[]#['state-18250-%03d.dtk' % x for x in range(24)]
# } for rn in range(10)]


def sample_point_fn(cb, sample_dimension_values):

    # require multinode to read in burn-in
    cb.update_params({'Simulation_Duration': sample_dimension_values['Serialization'],
                      'Spatial_Output_Channels': ['New_Diagnostic_Prevalence', 'Population', 'Prevalence'],
                      'Serialization_Time_Steps': [sample_dimension_values['Serialization']],
                      'New_Diagnostic_Sensitivity': 50
                      })

    # also need to pick up serialization path to load serialized file for each iteration.
    if sample_dimension_values['NodeIDs'] :

        # adjust the start date of VMW campaigns
        for event in cb.campaign['Events']:
            if event['Start_Day'] < sample_dimension_values['Serialization']:
                event['Start_Day'] = sample_dimension_values['Serialization']

        add_drug_campaign(cb, 'MDA', 'DP', [sample_dimension_values['Serialization']],
                          coverage=0.5, nodes=sample_dimension_values['NodeIDs'], interval=30)

        # for the second round, we want to set the start time equal to the last day of the old sim.
        # We also want duration to be equal to the new duration value, and for it to serialize at the
        # proper point.
        cb.update_params({'Start_Time': sample_dimension_values['Serialization'],
                          'Simulation_Duration': sample_dimension_values['New_Duration'],
                          'Serialization_Time_Steps': [sample_dimension_values['Serialization']+
                                                       sample_dimension_values['New_Duration']]})
        
    if 'Serialized_Population_Path' in sample_dimension_values:
        cb.set_param('Serialized_Population_Path',sample_dimension_values['Serialized_Population_Path'])
        
    if 'Serialized_Population_Filenames' in sample_dimension_values:
        cb.set_param('Serialized_Population_Filenames',sample_dimension_values['Serialized_Population_Filenames'])

    tags = {'Prevalence_date':sample_dimension_values['Prevalence_date'],
            'Prevalence_threshold': sample_dimension_values['Prevalence_threshold'],
            'Serialization': sample_dimension_values['New_Duration'] if sample_dimension_values['NodeIDs'] else
            sample_dimension_values['Serialization']}

    tags.update(cb.set_param('Run_Number', sample_dimension_values['Run_Number']))

    return tags

# sp.override_block('LOCAL')
calib_manager = CalibManager(name=sim_name,
                             config_builder=cb,
                             map_sample_to_model_input_fn=sample_point_fn,
                             sites=sites,
                             next_point=GenericIterativeNextPoint(initial_state),
                             sim_runs_per_param_set=1,
                             max_iterations=1,
                             plotters=[])

run_calib_args = {}

if __name__ == "__main__":
    # The following line would resume from iteration 0 at the step analyze
    # The available steps are: commission, analyze, next_point
    # calib_manager.resume_from_iteration(iteration=0, iter_step='analyze')
    # For now cleanup automatically
    calib_manager.cleanup()
    calib_manager.run_calibration()
