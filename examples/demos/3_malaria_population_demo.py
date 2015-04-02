import os
import json
import dtk_utils as utils
import dtk_demos as demos
import dtk_plots as plots

# specify demo-specific variables
geography     = "Zambia"
sim_type      = "MALARIA_SIM"
config_name   = "base_malaria_config.json"
campaign_name = "empty_campaign.json"

# load config/campaign
os.chdir(sim_type)
config, campaign = utils.load_config_campaign(config_name, campaign_name)

# modify config values
config["parameters"]["Simulation_Duration"] = 3 * 365  # three years

# DEMO: modify the config for speed
output_directory  = "baseline"
config = demos.speedup_malaria_sim(config)

# DEMO: add a mass-screen-and-treat campaign
#output_directory = "MSAT_campaign"
#config, campaign = demos.MSAT_campaign(config, campaign)
#config["parameters"]["Malaria_Drug_Params"]["Artemether_Lumefantrine"].update(AL_PQ_mod_params)

# DEMO: add a mass-drug-administration campaign
#output_directory = "MDA_campaign"
#config, campaign = demos.MDA_campaign(config, campaign)

# run the simulation
utils.run_dtk(output_directory, geography, config, campaign)
#os.chdir(output_directory)

# PLOT: vector species + human disease output
plots.plot_all( os.getcwd(), sim_type )

# PLOT: compare baseline + campaign
#plots.compare_sim_list( [ "baseline", "MSAT_campaign", "MSAT_campaign_rapid_PCR", "MDA_campaign" ] )
