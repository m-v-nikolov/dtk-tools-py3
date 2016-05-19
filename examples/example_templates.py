import os
from dtk.utils.builders.TemplateHelper import TemplateHelper
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from simtools.ModBuilder import ModBuilder

plugin_files_dir = 'Templates'

# Create an instance of the TemplateHelper helper class
templates = TemplateHelper()

# Build static params
static_params = {
    'CAMPAIGN.Demographic_Coverage__KP_Seeding_15_24': 0.01,
    'CAMPAIGN.Demographic_Coverage__KP_Seeding_25_49': 0.02,
    'DEMOGRAPHICS.Society__KP_Harare.TRANSITORY.Pair_Formation_Parameters.Formation_Rate_Constant': 1/365.0,
    'DEMOGRAPHICS.Society__KP_Manicaland.INFORMAL.Relationship_Parameters.Condom_Usage_Probability.Max': 1,
    'CONFIG.Campaign_Filename': 'campaign.json'
}

templates.set_static_params(static_params)

# Build and set the dynamic header and table
header = [  'CAMPAIGN.Start_Year__KP_Seeding_Year', 'DEMOGRAPHICS.Society__KP_Bulawayo.TRANSACTIONAL.Relationship_Parameters.Coital_Act_Rate' ]
table = [
            [ 1980, 1 ],
            [ 1990, 2]
        ]
templates.set_dynamic_header_table( header, table )

templates.add_template( os.path.join(plugin_files_dir, 'campaign.json') )

templates.add_template( os.path.join(plugin_files_dir, 'Demographics.json') )
templates.add_template( os.path.join(plugin_files_dir, 'PFA_Overlay.json') )
templates.add_template( os.path.join(plugin_files_dir, 'Accessibility_and_Risk_IP_Overlay.json') )
templates.add_template( os.path.join(plugin_files_dir, 'Risk_Assortivity_Overlay.json') )

config_builder = DTKConfigBuilder.from_files( os.path.join(plugin_files_dir, 'config.json') )

experiment_builder = ModBuilder( templates.experiment_builder() )

run_sim_args =  {'config_builder': config_builder,
                 'exp_builder': experiment_builder,
                 'exp_name': 'Zimbabwe'}

if __name__ == "__main__":
    from dtk.utils.core.DTKSetupParser import DTKSetupParser
    from simtools.ExperimentManager import ExperimentManagerFactory

    sm = ExperimentManagerFactory.from_model(DTKSetupParser('simulator.cfg').get('BINARIES', 'exe_path'), 'LOCAL')
    sm.run_simulations(**run_sim_args)

