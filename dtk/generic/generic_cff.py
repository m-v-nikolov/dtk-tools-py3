from climate_cff import *
from demographic_cff import *
from migration_cff import *
from mixing_pools_cff import *
from generic_disease_cff import *

generic_params = {
    "Config_Name": "", ###
    "Campaign_Filename": "campaign.json", 
    "Enable_Interventions": 1, 
    "Enable_Spatial_Output": 0,
    "Enable_Property_Output": 0,
    "Enable_Timestep_Channel_In_Report": 0,
    "Enable_Heterogeneous_Intranode_Transmission": 0,

    "Geography": "", ###
    "Node_Grid_Size": 0.042,             ###

    "Random_Type": "USE_PSEUDO_DES", 
    "Run_Number": 5, 
    "Simulation_Duration": 1825, 
    "Simulation_Timestep": 1, 
    "Simulation_Type": "",    ###
    "Start_Time": 0,
    
    "Num_Cores": 1, 
    "Python_Script_Path": "",
    "Serialization_Test_Cycles": 0,

    "Load_Balance_Filename": "", 
    "Load_Balance_Scheme": "STATIC"
}

generic_params.update(climate_params)
generic_params.update(demographic_params)
generic_params.update(generic_disease_params)
generic_params.update(no_migration_params)
generic_params.update(mixing_pool_params)
