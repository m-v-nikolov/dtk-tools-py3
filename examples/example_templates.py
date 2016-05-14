import os
from dtk.utils.builders.TemplateHelper import TemplateHelper
from dtk.utils.core import DTKConfigBuilder

plugin_files_dir = 'Templates'

# Create an instance of the TemplateHelper helper class
templates = TemplateHelper()

# Build static params
campaign_static_params = {
    'Demographic_Coverage__KP_Seeding_15_24': 0.01,
    'Demographic_Coverage__KP_Seeding_25_49': 0.02
}

demographic_static_params = {
    'DEMOGRAPHICS.Society__KP_Harare.TRANSITORY.Pair_Formation_Parameters.Formation_Rate_Constant': 1/365.0,
    'DEMOGRAPHICS.Society__KP_Manicaland.INFORMAL.Relationship_Parameters.Condom_Usage_Probability.Max': 1
}

# Build and set the dynamic header and table
header = [  'CAMPAIGN.Start_Year__KP_Seeding_Year', 'DEMOGRAPHICS.Society__KP_Bulawayo.TRANSACTIONAL.Relationship_Parameters.Coital_Act_Rate' ]
table = [
            [ 1980, 1 ],
            [ 1990, 2]
        ]
templates.set_dynamic_header_table( header, table )


# Add templates
templates.add_template( os.path.join(plugin_files_dir, 'campaign.json'), campaign_static_params )
templates.add_template( os.path.join(plugin_files_dir, 'PFA_Overlay.json'), demographic_static_params )

config_builder = DTKConfgBuilder.from_files( os.path.join(plugin_files_dir, 'config.json') )
experiment_builder = templates.experiment_builder()

run_sim_args =  {'config_builder': config_builder,
                 'exp_builder': experiment_builder,
                 'exp_name': 'Zimbabwe'}

if __name__ == "__main__":
    from dtk.utils.core.DTKSetupParser import DTKSetupParser
    from simtools.ExperimentManager import ExperimentManagerFactory

    sm = ExperimentManagerFactory.from_model(DTKSetupParser('simulator.cfg').get('BINARIES', 'exe_path'), 'LOCAL')
    sm.run_simulations(**run_sim_args)

