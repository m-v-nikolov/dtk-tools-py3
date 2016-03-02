import copy

waypoints_home_params = {
    "Migration_Model": "FIXED_RATE_MIGRATION", 
    "Migration_Pattern": "WAYPOINTS_HOME", 
    "Roundtrip_Waypoints": 5, ###
    "Enable_Migration_Heterogeneity": 0, 

    "Enable_Air_Migration": 0, 
    "Air_Migration_Filename": "", 
    "x_Air_Migration": 1, 
    "Air_Migration_Roundtrip_Duration"    : 0,
    "Air_Migration_Roundtrip_Probability" : 0,

    "Enable_Local_Migration": 0, 
    "Local_Migration_Filename": "", 
    "x_Local_Migration": 1, 
    "Local_Migration_Roundtrip_Duration"       : 0,
    "Local_Migration_Roundtrip_Probability"    : 0,

    "Enable_Regional_Migration": 0, 
    "Regional_Migration_Filename": "", 
    "x_Regional_Migration": 1, 
    "Regional_Migration_Roundtrip_Duration"    : 0,
    "Regional_Migration_Roundtrip_Probability" : 0,

    "Enable_Sea_Migration": 0, 
    "Sea_Migration_Filename": "", 
    "x_Sea_Migration": 1,
    "Sea_Migration_Roundtrip_Duration"         : 0,
    "Sea_Migration_Roundtrip_Probability"      : 0,
    "Enable_Sea_Demographics_Modifiers"        : 0,
    "Sea_Demographics_Modifier_Adult_Males"    : 1.0,
    "Sea_Demographics_Modifier_Adult_Females"  : 0.0,
    "Sea_Demographics_Modifier_Child_Males"    : 0.0,
    "Sea_Demographics_Modifier_Child_Females"  : 0.0,
    "Enable_Sea_Family_Migration"              : 0,
    "Sea_Family_Migration_Probability"         : 0.2
}

single_roundtrip_params = copy.deepcopy(waypoints_home_params)
single_roundtrip_params.update({
    "Migration_Pattern": "SINGLE_ROUND_TRIPS", 

    "Air_Migration_Roundtrip_Duration": 7, 
    "Air_Migration_Roundtrip_Probability": 0.8,

    "Local_Migration_Roundtrip_Duration": 0.5, 
    "Local_Migration_Roundtrip_Probability": 0.95,

    "Regional_Migration_Roundtrip_Duration": 7, 
    "Regional_Migration_Roundtrip_Probability": 0.1,

    "Sea_Migration_Roundtrip_Duration": 5, 
    "Sea_Migration_Roundtrip_Probability": 0.25,
    "Enable_Sea_Demographics_Modifiers"        : 0,
    "Sea_Demographics_Modifier_Adult_Males"    : 1.0,
    "Sea_Demographics_Modifier_Adult_Females"  : 0.0,
    "Sea_Demographics_Modifier_Child_Males"    : 0.0,
    "Sea_Demographics_Modifier_Child_Females"  : 0.0,
    "Enable_Sea_Family_Migration"              : 0,
    "Sea_Family_Migration_Probability"         : 0.2
})

no_migration_params = copy.deepcopy(waypoints_home_params)
no_migration_params.update({ "Migration_Model": "NO_MIGRATION" })
