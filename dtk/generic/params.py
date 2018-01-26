from dtk.generic import climate, demographics, disease, migration

params = {
    "Config_Name": "", ###,
    "Valid_Intervention_States": [],
    "Campaign_Filename": "campaign.json",
    "Enable_Interventions": 1,
    "Enable_Spatial_Output": 0,
    "Enable_Property_Output": 0,
    "Enable_Timestep_Channel_In_Report": 0,
    "Enable_Default_Reporting": 1,
    "Enable_Heterogeneous_Intranode_Transmission": 0,
    "Report_Event_Recorder": 0,
    "Enable_Immunity_Distribution": 0,
	"Enable_Maternal_Infection_Transmission": 0,
	"Enable_Maternal_Protection": 0,


    "Enable_Skipping": 0,

    "Listed_Events": [],
    "Minimum_Adult_Age_Years" : 15,

    "Vector_Migration_Base_Rate": 0.5,

    "Geography": "", ###
    "Node_Grid_Size": 0.042, ###
    "Default_Geography_Initial_Node_Population": 100,
    "Default_Geography_Torus_Size": 10,

    "Random_Type": "USE_PSEUDO_DES",
    "Run_Number": 5,
    "Simulation_Duration": 1825,
    "Simulation_Timestep": 1,
    "Simulation_Type": "", ###
    "Start_Time": 0,
    
    "Num_Cores": 1,
    "Python_Script_Path": "",

    "Load_Balance_Filename": "",
    "Load_Balance_Scheme": "STATIC",

    "Valid_Intervention_States" : ['None']
}

params.update(climate.params)
params.update(demographics.params)
params.update(disease.params)
params.update(migration.no_migration_params)
