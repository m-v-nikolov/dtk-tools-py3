import copy

from vector_species_cff import set_params_by_species
from larval_habitat_cff import *

# --------------------------------------------------------------
# Cohort model parameters
# --------------------------------------------------------------

vector_disease_params = {
    "Incubation_Period_Distribution": "FIXED_DURATION",
    "Base_Incubation_Period": 25, ##

    "Infectious_Period_Distribution": "EXPONENTIAL_DURATION", 
    "Base_Infectious_Period": 180, 
    "Base_Infectivity": 1,

    "Enable_Superinfection": 1, 
    "Max_Individual_Infections": 5, 
    "Infection_Updates_Per_Timestep": 1 ###
}

vector_cohort_params = {
    "Vector_Sampling_Type": "VECTOR_COMPARTMENTS_NUMBER", 
    "Mosquito_Weight": 1, 

    "Enable_Temperature_Dependent_Feeding_Cycle": 0,
    "Enable_Vector_Aging": 0, 
    "Enable_Vector_Migration": 0, 
    "Enable_Vector_Migration_Human": 0, 
    "Enable_Vector_Migration_Local": 0, 
    "Enable_Vector_Migration_Wind": 0, 

    "Age_Dependent_Biting_Risk_Type" : "SURFACE_AREA_DEPENDENT",
    "Newborn_Biting_Risk_Multiplier" : 0.2, # for LINEAR option (also picked up by InputEIR)
    "Human_Feeding_Mortality": 0.1, 

    "Vector_Sugar_Feeding_Frequency": "VECTOR_SUGAR_FEEDING_NONE", 
    "Wolbachia_Infection_Modification": 1.0, 
    "Wolbachia_Mortality_Modification": 1.0,
    "HEG_Homing_Rate": 0.0,
    "HEG_Fecundity_Limiting": 0.0,
    "HEG_Model": "OFF",

    "x_Temporary_Larval_Habitat": 1
}

vector_params = copy.deepcopy(vector_cohort_params)
vector_params.update(vector_disease_params)
vector_params.update(larval_habitat_params)

vector_params = set_params_by_species( vector_params, [ "arabiensis", "funestus", "gambiae" ] )

# --------------------------------------------------------------
# Individual-mosquito model (rather than cohort-based model)
# --------------------------------------------------------------

vector_individual_params = copy.deepcopy(vector_cohort_params)
vector_individual_params["Vector_Sampling_Type"] = "TRACK_ALL_VECTORS"

# --------------------------------------------------------------
# Using VECTOR_SIM as a vivax model
# --------------------------------------------------------------

vector_vivax_semitropical_params = copy.deepcopy(vector_disease_params)
vector_vivax_semitropical_params.update({
    "Incubation_Period_Distribution": "FIXED_DURATION",
    "Base_Incubation_Period": 18, # shorter time until gametocyte emergence

    "Infectious_Period_Distribution": "EXPONENTIAL_DURATION", 
    "Base_Infectious_Period": 240, # Guadalcanal, East Timor
    "Base_Infectivity": 1,

    "Enable_Superinfection": 0, 
    "Max_Individual_Infections": 1, 
    })

vector_vivax_chesson_params = copy.deepcopy(vector_vivax_semitropical_params)
vector_vivax_chesson_params.update({
    "Base_Infectious_Period": 40, # French Guiana 
    })
