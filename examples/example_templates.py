import os
from dtk.utils.builders.TemplateHelper import TemplateHelper
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from simtools.ModBuilder import ModBuilder

# The following directory holds the plugin files
plugin_files_dir = 'Templates'

# Create an instance of the TemplateHelper helper class
templates = TemplateHelper()

# The following "static" parameters will be applied for every simulation
static_params = {
    'CONFIG.Base_Population_Scale_Factor': 0.005,
    'CAMPAIGN.Demographic_Coverage__KP_Seeding_15_24': 0.01,
    'CAMPAIGN.Demographic_Coverage__KP_Seeding_25_49': 0.02,
    'DEMOGRAPHICS.Society__KP_Harare.TRANSITORY.Pair_Formation_Parameters.Formation_Rate_Constant': 1/365.0,
    'DEMOGRAPHICS.Society__KP_Manicaland.INFORMAL.Relationship_Parameters.Condom_Usage_Probability.Max': 1
}
templates.set_static_params(static_params)

# The following "dynamic" parameters will be set on a per-simulation basis.
# The header containes the parameter names
# The table containes the parameter values.  One simulation will be created for each row.
header = [  'CONFIG.Campaign_Filename', 'CAMPAIGN.Start_Year__KP_Seeding_Year', 'DEMOGRAPHICS.Society__KP_Bulawayo.TRANSACTIONAL.Relationship_Parameters.Coital_Act_Rate' ]
table = [
            [ 'campaign.json', 1980, 1 ],
            [ 'campaign_outbreak_only.json', 1990, 2]
        ]
templates.set_dynamic_header_table( header, table )


# Now we add templates.  Templates can replace the campaign or demographics files.
# When you use a template, you can 
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

