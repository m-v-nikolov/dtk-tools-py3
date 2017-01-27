"""
The philosophy of "templates" is to manually augment existing files with special tags that facilitate referencing.

This example highlights features of template-based input file manipulation building on 
an EMOD-HIV scenario: Scenarios/STIAndHIV/04_Health_Care/4_3_Health_Care_Model_Baseline.

The scenario has a config, campaign, and three demographic templates.  Here, we are going to:
* Edit parameters in config json
* Switch between two different campaign json files, both of which have been lightly marked with __KP tags
* Use tags to reference and subsequently edit parameters in campaign json
* Edit parameters in one of the three demographic files, the other two come from the InputFiles folder.  The file we will edit has been augmented with tags.

Template files, e.g. the ones we're going to generate on a per-simulation basis, will come from the plugin_files_dir.
"""

import os
from dtk.utils.builders.TemplateHelper import TemplateHelper
from dtk.utils.builders.ConfigTemplate import ConfigTemplate
from dtk.utils.builders.TaggedTemplate import CampaignTemplate, DemographicsTemplate
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from simtools.ModBuilder import ModBuilder
from simtools.SetupParser import SetupParser

# For example only -- Force the selected block to be EXAMPLE
SetupParser("EXAMPLE")

# The following directory holds the plugin files for this example.
plugin_files_dir = 'Templates'

"""
Create templates.  Templates can be used as config, campaign, or demographics files.

Templates can contain tagged parameters, typically Param_Name__KP_Some_Informative_String.  Parameters targeting these templates reference the __KP-tagged parameter names, see below When setting the parameter, everything after and including the tag will be removed, leaving just the parameter name, e.g. Param_Name in this example.  Tags need not be set at the root level, they can be placed deep in a nested json file and the system will automatically complete their json path(s).  Any given tag can be repeated in several locations in a file, and even across several files.

Active templates will be written to the working directly.

Note, you could easily use a different tag for each file / file type (config vs campaign vs demographics), but I have not demonstrated that here.
"""
cfg = ConfigTemplate.from_file( os.path.join(plugin_files_dir, 'config.json') )
cpn = CampaignTemplate.from_file( os.path.join(plugin_files_dir, 'campaign.json'), '__KP' )   # Here is how you set the tag, "__KP", for campaign, demographics, and potentially also config files
cpn_outbreak = CampaignTemplate.from_file( os.path.join(plugin_files_dir, 'campaign_outbreak_only.json') ) # These get the default tag, which is also "__KP"
demog_pfa = DemographicsTemplate.from_file( os.path.join(plugin_files_dir, 'pfa_overlay.json') )

# You can query and obtain values from templates.  Because some parameters can exist in multiple locations, i.e. tagged parameters, get_param return a tuple of (paths, values).\
demo_key = 'Start_Year__KP_Seeding_Year'
if cpn.has_param(demo_key):
    print "Demo getting values of %s:" % demo_key
    (paths, values) = cpn.get_param(demo_key)
    for (path, value) in zip( paths, values ):
        print '\t%s: %f'%(path, value)

# Set "static" parameters in these files.  These "static" parameters will be applied to every input file generated.
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

cfg.set_params( static_config_params )              # <-- Set static config parameters
cpn.set_params( static_campaign_params )            # <-- Set static campaign parameters for campaign.json
cpn_outbreak.set_params( static_campaign_params )   # <-- Set static campaign parameters for campaign_outbreak_only.json

demo_key = static_demog_params.keys()[0]
demo_value = static_demog_params.values()[0]
(paths,before) = demog_pfa.get_param( demo_key )
demog_pfa.set_params( static_demog_params )         # <-- Demo setting tagged parameter(s) in demographics file
(_,after) = demog_pfa.get_param( demo_key )
print 'Demo setting of %s to %f:' % (demo_key, demo_value)
for (p,b,a) in zip(paths, before, after):
    print '\t%s: %f --> %f'%(p,b,a)

"""
The following header and table contain the parameter names and values to be modified dynamically.  One simulation will be created for each row of the table.  Active template files are listed in the column with header keyword ACTIVE_TEMPLATES.  Additional tags can be added to each simulation using header keyword TAGS.
"""

header = [  'ACTIVE_TEMPLATES', 'Start_Year__KP_Seeding_Year', 'Condom_Usage_Probability__KP_INFORMAL.Max', 'Base_Infectivity', 'TAGS' ]
table = [
            [ [cfg, cpn,          demog_pfa], 1985, 0.95, 1.5e-3, {'Testing1a':None, 'Testing1b': 'Works'} ],
            [ [cfg, cpn_outbreak, demog_pfa], 1980, 0.50, 1.0e-3, {'Testing2':None} ]
        ]

"""
Create an instance of the TemplateHelper helper class and, if desired, give it templates to work with.
In this example, there's no need to set the campaign_template because it will be set dynamically from the table above.
TODO: Directly setting config_template, campaign_template, and demographic_templates doesn't feel right.  Should they have trivial setters?
"""
templates = TemplateHelper()

# Give the header and table to the template helper
templates.set_dynamic_header_table( header, table )

# Let's use a standard DTKConfigBuilder.
# Note, you can statically override config parameters here independently from the tagging system.  In this case, static parameters provided here will be overridden by the config template if the config template is activated.
config_builder = DTKConfigBuilder.from_files(
    os.path.join(plugin_files_dir, 'config.json'),
    os.path.join(plugin_files_dir, 'campaign.json')
 )

# For the experiment builder in the example, we use a ModBuilder from_combos to run
# each of the configurations for two separate run numbers.
experiment_builder = ModBuilder.from_combos(
    templates.get_modifier_functions(), # <-- Do this first!
    [ModBuilder.ModFn(DTKConfigBuilder.set_param, 'Run_Number', rn) for rn in range(2,4)]
)

run_sim_args =  {'config_builder': config_builder,
                 'exp_builder': experiment_builder,
                 'exp_name': 'TemplateDemo'}

if __name__ == "__main__":
    from simtools.ExperimentManager import ExperimentManagerFactory

    exp_manager = ExperimentManagerFactory.from_setup(SetupParser())
    exp_manager.run_simulations(**run_sim_args)

