import copy

waypoints_home_params = {
    "Migration_Model": "FIXED_RATE_MIGRATION", 
    "Migration_Pattern": "WAYPOINTS_HOME", 
    "Roundtrip_Waypoints": 5, ###
    "Enable_Migration_Heterogeneity": 0, 

    "Enable_Air_Migration": 0, 
    "Air_Migration_Filename": "", 
    "x_Air_Migration": 1, 

    "Enable_Local_Migration": 0, 
    "Local_Migration_Filename": "", 
    "x_Local_Migration": 1, 

    "Enable_Regional_Migration": 0, 
    "Regional_Migration_Filename": "", 
    "x_Regional_Migration": 1, 

    "Enable_Sea_Migration": 0, 
    "Sea_Migration_Filename": "", 
    "x_Sea_Migration": 1
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
})

no_migration_params = copy.deepcopy(waypoints_home_params)
no_migration_params.update({ "Migration_Model": "NO_MIGRATION" })
