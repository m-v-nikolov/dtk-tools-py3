import os
import json
import dtk_utils as utils
import dtk_demos as demos
import dtk_plots as plots
from dtk_drugs import AL_mod_params, AL_PQ_mod_params

# specify demo-specific variables
geography     = "Zambia"
sim_type      = "MALARIA_SIM"
config_name   = "base_malaria_config.json"
campaign_name = "empty_campaign.json"

# load config/campaign
os.chdir(sim_type)
config, campaign = utils.load_config_campaign(config_name, campaign_name)

# modify config values
config["parameters"]["Simulation_Duration"] = 8 * 365  # eight years

# DEMO: modify the config for speed
output_directory  = "spatial"
config = demos.speedup_malaria_sim(config)

# DEMO: set-up multi-node demographics/migration/etc.
config = demos.setup_spatial_sim(config)

# DEMO: add an MDA campaign
config, campaign = demos.MDA_campaign(config, campaign)
config["parameters"]["Malaria_Drug_Params"]["Artemether_Lumefantrine"].update(AL_PQ_mod_params)

# DEMO: add a drug-resistant outbreak in one node
campaign = demos.drug_resistant_outbreak(campaign)

# run the simulation
utils.run_dtk(output_directory, geography, config, campaign)
#os.chdir(output_directory)

# PLOT: vector species + human disease output
plots.plot_all( os.getcwd(), sim_type )

# PLOT: spatial distribution of EIR and prevalence by node
#plots.plot_spatial( os.getcwd(), sim_type )
