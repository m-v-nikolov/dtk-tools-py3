demographic_params = {

    "Demographics_Filename": "", 

    "Population_Scale_Type": "FIXED_SCALING", 
    "Base_Population_Scale_Factor": 1, 

    "Enable_Aging": 1, 
    "Age_Initialization_Distribution_Type": "DISTRIBUTION_SIMPLE", 

    "Enable_Demographics_Birth": 1, 
    "Enable_Demographics_Gender": 1, 
    "Enable_Demographics_Initial": 1, 
    "Enable_Demographics_Other": 1, 
    "Enable_Demographics_Reporting": 1, 

    "Enable_Immunity_Initialization_Distribution": 0, 

    "Enable_Vital_Dynamics": 1, 
    "Enable_Nondisease_Mortality": 1, 
    "Enable_Birth": 1, 
    "Birth_Rate_Dependence": "POPULATION_DEP_RATE", 
    "x_Birth": 1, 

    "Enable_Disease_Mortality": 0, 
    "Base_Mortality": 0, 
    "Mortality_Time_Course": "DAILY_MORTALITY",
    "x_Other_Mortality": 1, 

    "Individual_Sampling_Type": "TRACK_ALL", 
    "Base_Individual_Sample_Rate": 1,  ## all parameters below are unused without sampling
    "Max_Node_Population_Samples": 40, 
    "Sample_Rate_0_18mo": 1, 
    "Sample_Rate_10_14": 1, 
    "Sample_Rate_15_19": 1, 
    "Sample_Rate_18mo_4yr": 1, 
    "Sample_Rate_20_Plus": 1, 
    "Sample_Rate_5_9": 1, 
    "Sample_Rate_Birth": 2

}
