import os
from dtk.utils.builders.TemplateHelper import TemplateHelper
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from simtools.ModBuilder import ModBuilder

# The following directory holds the plugin files.
plugin_files_dir = 'Templates'

# The following "static" parameters will be applied for every simulation.
static_params = {
    'CONFIG.Base_Population_Scale_Factor': 0.005,
    'CAMPAIGN.Demographic_Coverage__KP_Seeding_15_24': 0.01,
    'CAMPAIGN.Demographic_Coverage__KP_Seeding_25_49': 0.02,
    'DEMOGRAPHICS.Society__KP_Harare.TRANSITORY.Pair_Formation_Parameters.Formation_Rate_Constant': 1/365.0,
    'DEMOGRAPHICS.Society__KP_Manicaland.INFORMAL.Relationship_Parameters.Condom_Usage_Probability.Max': 1
}

# Create an instance of the TemplateHelper helper class with the static parameters.
templates = TemplateHelper(static_params)

# The following "dynamic" parameters will be set on a per-simulation basis.
# The header containes the parameter names.
# The table containes the parameter values.  One simulation will be created for each row.
header = [  'CONFIG.Campaign_Filename', 'CAMPAIGN.Start_Year__KP_Seeding_Year', 'DEMOGRAPHICS.Society__KP_Bulawayo.INFORMAL.Relationship_Parameters.Coital_Act_Rate' ]
table = [
            [ 'campaign_outbreak_only.json', 1990, 2],
            [ 'campaign.json', 1980, 1 ]
        ]
templates.set_dynamic_header_table( header, table )

# Now we add templates.  Templates can be used as campaign or demographics files.
# Templates are activated by filename.  For example, if Campaign_Filename is 
# 'campaign_outbreak_only.json' in the config.json file and a template with matching
# filename exists has been added, as below, this template will be "activated."
#
# Active templates can contain tagged parameters, typically Param_Name__KP_some_string.
# Parameters targeting these templates reference the __KP tags, as above.
# When setting the parameter, everything after and including the tag, "__KP"
# will be removed, leaving just Param_Name in this example.  Tags need not be set
# at the root level, they can be placed deep in a nested json file and the system
# will automatically complete their path(s).
# A particular can exist can be repeated in several locations in a file, and even
# across several files.
#
# Note that you can set CONFIG.Campaign_Filename and CONFIG.Demographics_Filenames
# statically or dynamically above, and the corresponding templates will be activated.
#
# Active templates will be written to the working directly.
templates.add_template( os.path.join(plugin_files_dir, 'campaign.json') )
templates.add_template( os.path.join(plugin_files_dir, 'campaign_outbreak_only.json') )

templates.add_template( os.path.join(plugin_files_dir, 'Demographics.json') )
templates.add_template( os.path.join(plugin_files_dir, 'PFA_Overlay.json') )
templates.add_template( os.path.join(plugin_files_dir, 'Accessibility_and_Risk_IP_Overlay.json') )
templates.add_template( os.path.join(plugin_files_dir, 'Risk_Assortivity_Overlay.json') )

# Let's use a standard DTKConfigBuilder
config_builder = DTKConfigBuilder.from_files( os.path.join(plugin_files_dir, 'config.json') )

# For the experiment builder in the example, we use a ModBuilder from_combos to run
# each of the configurations for two separate run numbers.
experiment_builder = ModBuilder.from_combos(
    templates.experiment_builder(),
    [ModBuilder.ModFn(DTKConfigBuilder.set_param, 'CONFIG.Run_Number', rn) for rn in range(2,4)]
)

run_sim_args =  {'config_builder': config_builder,
                 'exp_builder': experiment_builder,
                 'exp_name': 'Zimbabwe'}

if __name__ == "__main__":
    from dtk.utils.core.DTKSetupParser import DTKSetupParser
    from simtools.ExperimentManager import ExperimentManagerFactory

    sm = ExperimentManagerFactory.from_model(DTKSetupParser('simulator.cfg').get('BINARIES', 'exe_path'), 'LOCAL')
    sm.run_simulations(**run_sim_args)

