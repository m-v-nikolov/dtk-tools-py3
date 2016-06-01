'''
This example highlights features of template-based input file manipulation building on 
an EMOD-HIV scenario: Scenarios/STIAndHIV/04_Health_Care/4_3_Health_Care_Model_Baseline.

The scenario has a config, campaign, and three demographic templates.  Here, we are going to 
* Edit parameters in config json
* Switch between two different campaign json files, both of which have been lightly marked with __KP tags
* Use tags to reference and subsequently edit parameters in campaign json
* Edit parameters in one of the three demographic files, the other two come from the InputFiles folder.  This file has been augmented with tags.

Template files, e.g. the ones we're going to generate on a per-simulation basis, will come from the plugin_files_dir.

The philosophy of "templates" is to manually augment existing files with special tags that facilitate referencing.
'''

import os
from dtk.utils.builders.TemplateHelper import TemplateHelper
#from dtk.utils.builders.Templates import ConfigTemplate, CampaignTemplate, DemographicsTemplate
from dtk.utils.builders.ConfigTemplate import ConfigTemplate
from dtk.utils.builders.TaggedTemplate import CampaignTemplate, DemographicsTemplate
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from simtools.ModBuilder import ModBuilder

# The following directory holds the plugin files for this example.
plugin_files_dir = 'Templates'

'''
Create templates.  Templates can be used as config, campaign, or demographics files.

Templates can contain tagged parameters, typically Param_Name__KP_Some_Informative_String.  Parameters targeting these templates reference the __KP-tagged parameter names, see below When setting the parameter, everything after and including the tag will be removed, leaving just the parameter name, e.g. Param_Name in this example.  Tags need not be set at the root level, they can be placed deep in a nested json file and the system will automatically complete their json path(s).  Any given tag can be repeated in several locations in a file, and even across several files.

Active templates will be written to the working directly.

Note, you could easily use a different tag for each file / file type (config vs campaign vs demographics), but I have not demonstrated that here.
'''
cfg = ConfigTemplate.from_file( os.path.join(plugin_files_dir, 'config.json') )
print "TRUE  ?=", cfg.is_consumed_by_template('Base_Infectivity')
print "TRUE  ?=", cfg.is_consumed_by_template('STI_Network_Params_By_Property.NONE.Extra_Relational_Flag_Type')
print "FALSE ?=", cfg.is_consumed_by_template('Demographics_Filenames[10]')
print cfg.get_param('Demographics_Filenames[1]')


cpn = CampaignTemplate.from_file( os.path.join(plugin_files_dir, 'campaign.json'), '__KP' )   # Here is how you set the tag, "__KP", for campaign, demographics, and potentially also config files
print "FALSE ?=", cpn.is_consumed_by_template('Events[0]')
print "TRUE  ?=", cpn.is_consumed_by_template('Demographic_Coverage__KP_Seeding_15_24_Male')
print cpn.get_param('Events[0].Start_Year')


cpn_outbreak = CampaignTemplate.from_file( os.path.join(plugin_files_dir, 'campaign_outbreak_only.json') ) # These get the default tag, which is also "__KP"

demog_pfa = DemographicsTemplate.from_file( os.path.join(plugin_files_dir, 'pfa_overlay.json') )



'''
Set "static" parameters in these files.  These "static" parameters will be applied to every input file generated.
TODO: Would like to list parameters and feed to kwargs, but the periods make them invalid keywords
'''
static_config_params = {
    'Base_Population_Scale_Factor':  1/10000.0
}
static_campaign_params = {
    'Demographic_Coverage__KP_Seeding_15_24_Male': 0.035,
    'Intervention_Config__KP_STI_CoInfection_At_Debut.Demographic_Coverage': 0.055
}
static_demog_params = {
    'Relationship_Parameters__KP_TRANSITORY.Coital_Act_Rate': 0.5
}

before = cfg.get_param( static_config_params.keys()[0] )
cfg.set_params( static_config_params )
after = cfg.get_param( static_config_params.keys()[0] )
print "Before =: %s, After = %s" % (before, after)


before = cpn.get_param( static_campaign_params.keys()[0] )
cpn.set_params( static_campaign_params )
after = cpn.get_param( static_campaign_params.keys()[0] )
print "Before =: %s, After = %s" % (before, after)
cpn_outbreak.set_params( static_campaign_params )
demog_pfa.set_params( static_demog_params )

'''
The header and table contain the parameter names and values, respectively.  One simulation will be created for each row of the table.  Active templates are listed in the column with header keyword ACTIVE_TEMPLATES.  Additional tags can be added to each simulation using header keywork TAGS.
'''

header = [  'ACTIVE_TEMPLATES', 'Start_Year__KP_Seeding_Year', 'Condom_Usage_Probability__KP_INFORMAL.Max', 'Base_Infectivity', 'TAGS' ]
table = [
            [ [cfg, cpn,          demog_pfa], 1985, 0.95, 1.5e-3, ['Testing1'] ],
            [ [cfg, cpn_outbreak, demog_pfa], 1980, 0.50, 1.0e-3, ['Testing2'] ]
        ]

'''
Create an instance of the TemplateHelper helper class and, if desired, give it templates to work with.
In this example, there's no need to set the campaign_template because it will be set dynamically from the table above.
TODO: Directly setting config_template, campaign_template, and demographic_templates doesn't feel right.  Should they have trivial setters?
'''
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
    [ModBuilder.ModFn(DTKConfigBuilder.set_param, 'Run_Number', rn) for rn in range(2,4)],
    templates.get_modifier_functions()
)

run_sim_args =  {'config_builder': config_builder,
                 'exp_builder': experiment_builder,
                 'exp_name': 'TemplateDemo'}

if __name__ == "__main__":
    from simtools.SetupParser import SetupParser
    from simtools.ExperimentManager import ExperimentManagerFactory

    sm = ExperimentManagerFactory.from_model(SetupParser('simulator.cfg').get('BINARIES', 'exe_path'), 'LOCAL')
    sm.run_simulations(**run_sim_args)

