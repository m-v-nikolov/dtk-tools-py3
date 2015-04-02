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
config["parameters"]["Simulation_Duration"] = 365 # one year
config["parameters"]["Enable_Immunity_Initialization_Distribution"] = 1

# DEMO: modify the config/campaign for single patients
#output_directory  = "single_patients_no_vectors"
#config, campaign = demos.single_patient_import_no_vectors(config, campaign)

# DEMO: modify the config/campaign for drug trials
output_directory = "drug_trial"
config, campaign = demos.single_patient_prevalence_increase_no_vectors(config, campaign)
config, campaign = demos.drug_trial(config, campaign)

# DEMO: modify the config/campaign for vaccine challenge trial
#output_directory = "vaccine_challenge"
#config["parameters"]["Enable_Immunity_Initialization_Distribution"] = 0 # naive volunteers
#config, campaign = demos.single_patient_infectious_bite_challenge_no_vectors(config, campaign)
#config, campaign = demos.RTSS_vaccine_trial(config, campaign)

# custom output dlls
dlls = os.path.join(os.getcwd(), "matlab_patient_reporter")

# run the simulation
utils.run_dtk(output_directory, geography, config, campaign, dlls)
