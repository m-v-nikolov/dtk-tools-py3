"""
The philosophy of "templates" is to manually augment existing files with special tags that facilitate referencing.

This example highlights features of template-based input file manipulation building on 
an EMOD-HIV scenario: Scenarios/STIAndHIV/04_Health_Care/4_3_Health_Care_Model_Baseline.

The scenario has a config, campaign, and three demographic templates.  Here, we are going to:
* Edit parameters in config json
* Switch between two different campaign json files, both of which have been lightly marked with __KP tags
* Use tags to reference and subsequently edit parameters in campaign json
* Edit parameters in one of the three demographic files, the other two come from the InputFiles folder.
  The file we will edit has been augmented with tags.

Template files, e.g. the ones we're going to generate on a per-simulation basis, will come from the plugin_files_dir.
"""

import os

from dtk.utils.builders.ConfigTemplate import ConfigTemplate
from dtk.utils.builders.TaggedTemplate import CampaignTemplate, DemographicsTemplate
from dtk.utils.builders.TemplateHelper import TemplateHelper
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.ModBuilder import ModBuilder, ModFn
from simtools.SetupParser import SetupParser

# This block will be used unless overridden on the command-line
SetupParser.default_block = 'HPC'

# The following directory holds the plugin files for this example.
plugin_files_dir = 'Templates'

# Templates creation
# ==================
# Templates can be used as config, campaign, or demographics files.
#
# Templates can contain tagged parameters, typically Param_Name__KP_Some_Informative_String.
# Parameters targeting these templates reference the __KP-tagged parameter names,
# see below: when setting the parameter, everything after and including the tag will be removed,
# leaving just the parameter name, e.g. Param_Name in this example.
#
# Tags need not be set at the root level, they can be placed deep in a nested json file
# and the system will automatically complete their json path(s).
# Any given tag can be repeated in several locations in a file, and even across several files.
#
# Active templates will be written to the working directly.
#
# Note, you could easily use a different tag for each file / file type
# (config vs campaign vs demographics), but we have not demonstrated that here.
cfg = ConfigTemplate.from_file(template_filepath=os.path.join(plugin_files_dir, 'config.json'))
# Here is how you set the tag, "__KP", for campaign, demographics, and potentially also config files
cpn = CampaignTemplate.from_file(template_filepath=os.path.join(plugin_files_dir, 'campaign.json'), tag='__KP')
cpn_outbreak = CampaignTemplate.from_file(template_filepath=os.path.join(plugin_files_dir, 'campaign_outbreak_only.json'))
demog_pfa = DemographicsTemplate.from_file(template_filepath=os.path.join(plugin_files_dir, 'pfa_overlay.json'))

# Templates Querying
# ==================
# You can query and obtain values from templates.
# Because some parameters can exist in multiple locations, i.e. tagged parameters, get_param return a tuple of (paths, values).
# The example below is listing every places where the Start_Year__KP_Seesing_Year appears in the cpn template
demo_key = 'Start_Year__KP_Seeding_Year'
# the has_param allows to check if a template includes a KP parameter
if cpn.has_param(param=demo_key):
    print("Demo getting values of {}:".format(demo_key))
    # get_param returns all the paths and values for the particular KP parameter
    paths, values = cpn.get_param(param=demo_key)
    # Print the couple path:value
    for (path, value) in zip(paths, values):
        print("\t{}: {}".format(path, value))

# Static parameters
# =================
# Set "static" parameters in these files.
# These "static" parameters will be applied to every input file generated.
# The parameters are defined with dictionaries formatted as:
# {
#    'parameter':value
# }
static_config_params = {
    'Base_Population_Scale_Factor':  1/10000.0
}
static_campaign_params = {
    'Intervention_Config__KP_STI_CoInfection_At_Debut.Demographic_Coverage': 0.055,
    'Demographic_Coverage__KP_Seeding_15_24_Male': 0.035
}
static_demog_params = {
    'Relationship_Parameters__KP_TRANSITORY_and_INFORMAL.Coital_Act_Rate': 0.5
}
# Once we have the static parameters dictionaries, we need to apply them to our templates
cfg.set_params(static_config_params)              # <-- Set static config parameters
cpn.set_params(static_campaign_params)            # <-- Set static campaign parameters for campaign.json
cpn_outbreak.set_params(static_campaign_params)   # <-- Set static campaign parameters for campaign_outbreak_only.json

# Templates Querying and Setting
# ==============================
# This block of code demonstrates query/modifications of a tagged parameter in demographics file
# First we are retrieving:
# - the key (Relationship_Parameters__KP_TRANSITORY_and_INFORMAL.Coital_Act_Rate)
# - the value (0.5)
# from the static_demog_params
demo_key = static_demog_params.keys()[0]
demo_value = static_demog_params.values()[0]
# Then we are using get_param to get the paths and the current values in the template
# In this example, the current value is set to 0.33
paths, before = demog_pfa.get_param(demo_key)
# We are now setting the KP parameter to be 0.5 through the set_params function
demog_pfa.set_params(static_demog_params)
# Now we want to query again to check what is the new value and make sure it is 0.5
# The (_, after) notation means we do not care about the "paths" returned but just the new values
# The paths were already returned during the first call on get_param
_, after = demog_pfa.get_param(demo_key)
# Display the information
print("\nDemo setting of {} to {}:".format(demo_key, demo_value))
for (path, before_value, after_value) in zip(paths, before, after):
    print("\t{}: {} --> {}".format(path, before_value, after_value))
print("")

# Table of simulations
# ====================
# The following header and table contain the parameter names and values to be modified dynamically.
# One simulation will be created for each row of the table.
# Active template files are listed in the column with header keyword ACTIVE_TEMPLATES.
# Additional tags can be added to each simulation using header keyword TAGS.
# As shown below, the first simulation will use cfg, cpn and demo_pfa while the other one will use the cpn_outbreak
header = ['ACTIVE_TEMPLATES',
          'Start_Year__KP_Seeding_Year',
          'Condom_Usage_Probability__KP_INFORMAL.Max',
          'Base_Infectivity',
          'TAGS']
table = [
            [[cfg, cpn,          demog_pfa], 1985, 0.95, 1.5e-3, {'Testing1a': None, 'Testing1b': 'Works'}],
            [[cfg, cpn_outbreak, demog_pfa], 1980, 0.50, 1.0e-3, {'Testing2': None}]
        ]


# Initialize the template system
# ==============================
# Create an instance of the TemplateHelper helper class and, if desired, give it templates to work with.
# In this example, there's no need to set the campaign_template because it will be set dynamically from the table above.
templates = TemplateHelper()

# Give the header and table to the template helper
templates.set_dynamic_header_table(header, table)

# Let's use a standard DTKConfigBuilder.
config_builder = DTKConfigBuilder()
# ignore_missing is required when using templates
config_builder.ignore_missing = True

# Use the default COMPS 2.10 and the SamplesInput folder for input files
# See examples\AssetManagement\use_custom_executable.py for more information
config_builder.set_exe_collection('EMOD 2.10')

# For the experiment builder in the example, we use a ModBuilder from_combos to run
# each of the configurations for two separate run numbers.
# The first line needs to be the modifier functions coming from the templates
experiment_builder = ModBuilder.from_combos(
    templates.get_modifier_functions(), # <-- Do this first!
    [ModFn(DTKConfigBuilder.set_param, 'Run_Number', rn) for rn in range(2, 4)]
)

# This dictionary is used by the `dtk run` command line and allow to pass it some parameters
# If you are running through `python example_templates.py`, this dictionary is unused
run_sim_args = {
    'exp_builder': experiment_builder,
    'exp_name': 'TemplateDemo',
    'config_builder':config_builder
}

# This part is needed if you are running the script through `python example_templates.py`
# It is not used by the command line interface
if __name__ == "__main__":
    # The first thing to do is always to initialize the environment
    SetupParser.init()
    # We are creating an experiment manager for our experiment
    exp_manager = ExperimentManagerFactory.init()
    # Then create the simulations and run the experiment
    exp_manager.run_simulations(exp_name='TemplateDemo', config_builder=config_builder, exp_builder=experiment_builder)
    # The following line is allowing to wait for the experiment to complete successfully
    # and display the status every few seconds. It is optional.
    exp_manager.wait_for_finished(verbose=True)
    assert (exp_manager.succeeded())

