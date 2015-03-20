import copy

from malaria_infection_cff import *
from malaria_immunity_cff import *
from malaria_symptoms_cff import *
from ..vector.vector_species_cff import set_params_by_species
from ..interventions.malaria_drug_cff import malaria_drug_params

# --------------------------------------------------------------
# Malaria disease + drug parameters
# --------------------------------------------------------------

malaria_disease_params = {
    "Malaria_Model": "MALARIA_MECHANISTIC_MODEL", 
    "Malaria_Strain_Model": "FALCIPARUM_RANDOM_STRAIN"
}
malaria_disease_params.update(malaria_infection_params)
malaria_disease_params.update(malaria_immune_params)
malaria_disease_params.update(malaria_symptomatic_params)

malaria_params = copy.deepcopy(malaria_disease_params)
malaria_params["PKPD_Model"] = "FIXED_DURATION_CONSTANT_EFFECT"
malaria_params["Malaria_Drug_Params"] = malaria_drug_params

set_params_by_species( malaria_params, [ "arabiensis", "funestus", "gambiae" ], "MALARIA_SIM" )

# --------------------------------------------------------------
# Innate immunity only
# --------------------------------------------------------------

malaria_innate_only = copy.deepcopy(malaria_disease_params)
malaria_innate_only.update({
    "Antibody_Capacity_Growth_Rate": 0,
    "Max_MSP1_Antibody_Growthrate": 0,
    "Min_Adapted_Response": 0
})