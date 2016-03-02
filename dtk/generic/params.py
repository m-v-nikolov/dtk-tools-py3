import climate
import demographics
import migration
import disease

params = {
    "Config_Name": "", ###
    "Campaign_Filename": "campaign.json", 
    "Enable_Interventions": 1, 
    "Enable_Spatial_Output": 0,
    "Enable_Property_Output": 0,
    "Enable_Timestep_Channel_In_Report": 0,
    "Enable_Default_Reporting": 1,
    "Enable_Heterogeneous_Intranode_Transmission": 0,
    "Report_Event_Recorder": 0,

    "Listed_Events": [],
    "Minimum_Adult_Age_Years" : 15,

    "Geography": "", ###
    "Node_Grid_Size": 0.042, ###

    "Random_Type": "USE_PSEUDO_DES", 
    "Run_Number": 5, 
    "Simulation_Duration": 1825, 
    "Simulation_Timestep": 1, 
    "Simulation_Type": "", ###
    "Start_Time": 0,
    
    "Num_Cores": 1, 
    "Python_Script_Path": "",
    "Serialization_Test_Cycles": 0,

    "Load_Balance_Filename": "", 
    "Load_Balance_Scheme": "STATIC"
}

params.update(climate.params)
params.update(demographics.params)
params.update(disease.params)
params.update(migration.no_migration_params)