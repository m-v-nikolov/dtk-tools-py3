import copy

from ..vector.species import set_params_by_species
from ..interventions.malaria_drug_cff import malaria_drug_params

# --------------------------------------------------------------
# Malaria disease + drug parameters
# --------------------------------------------------------------

disease_params = {
    "Malaria_Model": "MALARIA_MECHANISTIC_MODEL", 
    "Malaria_Strain_Model": "FALCIPARUM_RANDOM_STRAIN"
}

infection_params = {
    "Infection_Updates_Per_Timestep": 8, ###
    "Enable_Superinfection": 1, 
    "Max_Individual_Infections": 3, ###

    "Mean_Sporozoites_Per_Bite": 11, 
    "Base_Sporozoite_Survival_Fraction": 0.25, 
    "Base_Incubation_Period": 7, ###
    "Merozoites_Per_Hepatocyte": 15000, 

    "Antibody_IRBC_Kill_Rate": 1.596, 
    "RBC_Destruction_Multiplier": 3.29, #3.5756
    "Merozoites_Per_Schizont": 16, 
    "Parasite_Switch_Type": "RATE_PER_PARASITE_7VARS", 

    # 150305 calibration by JG to Burkina data + 6 of Kevin's sites
    # N.B: severe disease re-calibration not done
    'Base_Gametocyte_Production_Rate' : 0.044,
    "Gametocyte_Stage_Survival_Rate": 0.82,
    'Antigen_Switch_Rate' : 2.96e-9,
    'Falciparum_PfEMP1_Variants' : 1112,
    'Falciparum_MSP_Variants' : 7,
    'MSP1_Merozoite_Kill_Fraction' : 0.43,
    'Falciparum_Nonspecific_Types' : 90,
    'Nonspecific_Antigenicity_Factor' : 0.42,
    'Base_Gametocyte_Mosquito_Survival_Rate' : 0.00088,

    "Number_Of_Asexual_Cycles_Without_Gametocytes": 1, 
    "Base_Gametocyte_Fraction_Male": 0.2, 
    "Enable_Sexual_Combination": 0
    }

immune_params = {
    "Antibody_CSP_Decay_Days": 90, 
    "Antibody_CSP_Killing_Inverse_Width": 1.5, 
    "Antibody_CSP_Killing_Threshold": 20, 

    "Innate_Immune_Variation_Type": "NONE",
    "Pyrogenic_Threshold": 1.5e4,
    "Fever_IRBC_Kill_Rate": 1.4, 

    "Max_MSP1_Antibody_Growthrate": 0.045, 
    "Antibody_Capacity_Growth_Rate": 0.09, 
    "Nonspecific_Antibody_Growth_Rate_Factor": 0.5, # multiplied by major-epitope number to get rate
    "Antibody_Stimulation_C50": 30, 
    "Antibody_Memory_Level": 0.34, 
    "Min_Adapted_Response": 0.05, 

    "Cytokine_Gametocyte_Inactivation": 0.01667, 

    "Maternal_Antibodies_Type": "SIMPLE_WANING",
    "Maternal_Antibody_Protection": 0.1327,
    "Maternal_Antibody_Decay_Rate": 0.01,

    "Erythropoiesis_Anemia_Effect": 3.5
    }

symptomatic_params = {
    "Anemia_Mortality_Inverse_Width": 150, 
    "Anemia_Mortality_Threshold": 1, 
    "Anemia_Severe_Inverse_Width": 100, 
    "Anemia_Severe_Threshold": 5,

    "Fever_Mortality_Inverse_Width": 1000, 
    "Fever_Mortality_Threshold": 10, 
    "Fever_Severe_Inverse_Width": 30.323, 
    "Fever_Severe_Threshold": 3.8719,

    "Parasite_Mortality_Inverse_Width": 100, 
    "Parasite_Mortality_Threshold": 3e6, 
    "Parasite_Severe_Inverse_Width": 7.931, 
    "Parasite_Severe_Threshold": 3.17351e5,

    "Clinical_Fever_Threshold_High": 1.5, 
    "Clinical_Fever_Threshold_Low": 0.5, 
    "Min_Days_Between_Clinical_Incidents": 14,

    "Fever_Detection_Threshold": 1, 
    "New_Diagnostic_Sensitivity": 0.025, # 40/uL
    "Parasite_Smear_Sensitivity": 0.1    # 10/uL
}

disease_params.update(infection_params)
disease_params.update(immune_params)
disease_params.update(symptomatic_params)

params = copy.deepcopy(disease_params)
params["PKPD_Model"] = "FIXED_DURATION_CONSTANT_EFFECT"
params["Malaria_Drug_Params"] = malaria_drug_params

set_params_by_species(params, ["arabiensis", "funestus", "gambiae"], "MALARIA_SIM")

# --------------------------------------------------------------
# Innate immunity only
# --------------------------------------------------------------

innate_only = copy.deepcopy(params)
innate_only.update({
    "Antibody_Capacity_Growth_Rate": 0,
    "Max_MSP1_Antibody_Growthrate": 0,
    "Min_Adapted_Response": 0
})