import copy

# --------------------------------------------------------------
# Larval habitat parameters
# --------------------------------------------------------------

larval_habitat_params = {
    "Egg_Hatch_Delay_Distribution": "NO_DELAY", 
    "Egg_Saturation_At_Oviposition": "SATURATION_AT_OVIPOSITION", 
    "Mean_Egg_Hatch_Delay": 0,
    "Rainfall_In_mm_To_Fill_Swamp": 1000.0, 
    "Semipermanent_Habitat_Decay_Rate": 0.01, 
    "Temporary_Habitat_Decay_Factor": 0.05, 
    "Larval_Density_Dependence": "UNIFORM_WHEN_OVERPOPULATION", 
    "Vector_Larval_Rainfall_Mortality": "NONE"
}

# --------------------------------------------------------------
# Notre Dame modifications for instar-specific behavior
# --------------------------------------------------------------

notre_dame_habitat_params = copy.deepcopy(larval_habitat_params)
ND_mod_params = {
    "Egg_Hatch_Delay_Distribution": "EXPONENTIAL_DURATION", 
    "Egg_Saturation_At_Oviposition": "NO_SATURATION", 
    "Mean_Egg_Hatch_Delay": 2,
    "Larval_Density_Dependence": "GRADUAL_INSTAR_SPECIFIC"
}
notre_dame_habitat_params.update(ND_mod_params)