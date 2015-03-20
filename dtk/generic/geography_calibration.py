from dtk.interventions.malaria_challenge import add_challenge_trial
from dtk.interventions.malaria_drug_campaign_cff import add_drugs,drug_params
from dtk.interventions.health_seeking import add_health_seeking
from dtk.interventions.input_EIR import add_InputEIR
from dtk.interventions.malaria_summary import add_summary_report
from dtk.interventions.malaria_survey import add_survey

geographies_config = {

    "Dapelogo" :     { "Geography": "Burkina",
                       "Demographics_Filename":      "Calibration\calibration_challenge.compiled.json", 
                       'Base_Population_Scale_Factor' : 10,
                       'Enable_Vital_Dynamics' : 0,
                       'Simulation_Duration' : 21915,
                       'Infection_Updates_Per_Timestep' : 8,
                       "Vector_Species_Names": [],
                       "Climate_Model" : "CLIMATE_CONSTANT" # no mosquitoes
                     },
    "Laye" :         { "Geography": "Burkina",
                       "Demographics_Filename":      "Calibration\calibration_challenge.compiled.json", 
                       'Base_Population_Scale_Factor' : 10,
                       'Enable_Vital_Dynamics' : 0,
                       'Simulation_Duration' : 21915,
                       'Infection_Updates_Per_Timestep' : 8,
                       "Vector_Species_Names": [],
                       "Climate_Model" : "CLIMATE_CONSTANT" # no mosquitoes
                     },

    "Matsari" :     { "Geography": "Garki_Single",
                       "Demographics_Filename":      "Calibration\calibration_challenge.compiled.json", 
                       'Base_Population_Scale_Factor' : 10,
                       'Enable_Vital_Dynamics' : 0,
                       'Simulation_Duration' : 21915,
                       'Infection_Updates_Per_Timestep' : 8,
                       "Vector_Species_Names": [],
                       "Climate_Model" : "CLIMATE_CONSTANT" # no mosquitoes
                     },
    "Rafin_Marke" : { "Geography": "Garki_Single",
                       "Demographics_Filename":      "Calibration\calibration_challenge.compiled.json", 
                       'Base_Population_Scale_Factor' : 10,
                       'Enable_Vital_Dynamics' : 0,
                       'Simulation_Duration' : 21915,
                       'Infection_Updates_Per_Timestep' : 8,
                       "Vector_Species_Names": [],
                       "Climate_Model" : "CLIMATE_CONSTANT" # no mosquitoes
                     },
    "Sugungum" :    { "Geography": "Garki_Single",
                       "Demographics_Filename":      "Calibration\calibration_challenge.compiled.json", 
                       'Base_Population_Scale_Factor' : 10,
                       'Enable_Vital_Dynamics' : 0,
                       'Simulation_Duration' : 21915,
                       'Infection_Updates_Per_Timestep' : 8,
                       "Vector_Species_Names": [],
                       "Climate_Model" : "CLIMATE_CONSTANT" # no mosquitoes
                     },

    "Namawala" :     { "Geography": "Namawala",
                       "Demographics_Filename":      "Calibration\calibration_challenge.compiled.json", 
                       'Base_Population_Scale_Factor' : 10,
                       'Enable_Vital_Dynamics' : 0,
                       'Simulation_Duration' : 21915,
                       'Infection_Updates_Per_Timestep' : 8,
                       "Vector_Species_Names": [],
                       "Climate_Model" : "CLIMATE_CONSTANT" # no mosquitoes
                     },

    "Dielmo" :       { "Geography": "Senegal_Gambia/Dielmo_Ndiop",
                       "Demographics_Filename":      "Calibration\calibration_challenge.compiled.json", 
                       'Base_Population_Scale_Factor' : 10,
                       'Enable_Vital_Dynamics' : 0,
                       'Simulation_Duration' : 21915,
                       'Infection_Updates_Per_Timestep' : 8,
                       "Vector_Species_Names": [],
                       "Climate_Model" : "CLIMATE_CONSTANT" # no mosquitoes
                      },

    "Ndiop" :        { "Geography": "Senegal_Gambia/Dielmo_Ndiop",
                       "Demographics_Filename":      "Calibration\calibration_challenge.compiled.json", 
                       'Base_Population_Scale_Factor' : 10,
                       'Enable_Vital_Dynamics' : 0,
                       'Simulation_Duration' : 21915,
                       'Infection_Updates_Per_Timestep' : 8,
                       "Vector_Species_Names": [],
                       "Climate_Model" : "CLIMATE_CONSTANT" # no mosquitoes
                      },

    "Malariatherapy" : {  "Geography": "Malariatherapy",
                          "Demographics_Filename": "Calibration\Malariatherapy_demographics.compiled.json", 
                          'Base_Population_Scale_Factor' : 2,
                          'Enable_Vital_Dynamics' : 0,
                          'Simulation_Duration' : 365,
                          'Infection_Updates_Per_Timestep' : 8,
                          "Vector_Species_Names": [],
                          "Climate_Model" : "CLIMATE_CONSTANT" # no mosquitoes in challenge trial setting
                      },

    "BFinf" :        { "Geography": "Burkina",
                       "Demographics_Filename":      "Calibration\Burkina Faso_Dapelogo_2.5arcmin_demographics.static.compiled.json;Calibration\Burkina Faso_Dapelogo_2.5arcmin_immune_init_150113_calib9.compiled.json", 
                       "Enable_Immunity_Initialization_Distribution":1,
                       'Base_Population_Scale_Factor' : 1,
                       'Enable_Vital_Dynamics' : 0,
                       'Simulation_Duration' : 1461,
                       'Infection_Updates_Per_Timestep' : 8,
                       "Vector_Species_Names": [],
                       "Climate_Model" : "CLIMATE_CONSTANT", # no mosquitoes
                       'Demographic_Coverage' : 0.95,
                       'Base_Gametocyte_Production_Rate' : 0.1,
                       "Gametocyte_Stage_Survival_Rate": 0.58,
                       'Antigen_Switch_Rate' : 2.83e-10,
                       'Falciparum_PfEMP1_Variants' : 1114,
                       'Falciparum_MSP_Variants' : 42,
                       'MSP1_Merozoite_Kill_Fraction' : 0.46,
                       'MSP2_Merozoite_Kill_Fraction' : 0.46,
                       'Falciparum_Nonspecific_Types' : 46,
                       'Nonspecific_Antigenicity_Factor' : 0.32,
                       'Max_Individual_Infections' : 3
                     }

}

geographies_campaigns = {

    'Malariatherapy' : { 'challenge bite' : 1,
                         'survey' : { 'survey_days' : [1],
                                      'interval' : geographies_config['Malariatherapy']['Simulation_Duration']-1,
                                      'number_reports' : 1,
                                      'description': 'Survey_Analyzer',
                                      'coverage' : 1}},

    'BFinf' : { 'immune_overlay' : '150113_calib9', 
                'survey' : { 'survey_days' : [730],
                              'interval' : geographies_config['BFinf']['Simulation_Duration']-1-730,
                              'number_reports' : 1,
                              'description': 'Survey_Analyzer',
                              'coverage' : 1},
                 'input EIR' : {'start_day' : 0,
                                'EIRs' : [1, 1, 1, 1, 1, 3, 27, 70, 130, 57, 29, 1]},
                 'health seeking' : {'start_day' : 0,
                                     'drugs' : ['Artemether', 'Lumefantrine'],
                                     'trigger': 'NewClinicalCase',
                                     'coverage': 0.8, 
                                     'seek': 0.6, 
                                     'rate': 0.2 }},

    'Dapelogo' : { 'input EIR' : {'start_day' : 0,
                                  'EIRs' : [1, 1, 1, 1, 1, 3, 27, 70, 130, 57, 29, 1]},
                   'health seeking' : {'start_day' : 0,
                                       'drugs' : ['Artemether', 'Lumefantrine'],
                                       'trigger': 'NewClinicalCase',
                                       'coverage': 0.8, 
                                       'seek': 0.6, 
                                       'rate': 0.2 },
                   'summary report' : { 'start_day' : 1,
                                        'interval' : 30.42,
                                        'number_reports' : 2000,
                                        'agebins' : [1000],
                                        'description': 'Monthly_Report'}},
                   
    'Laye' : { 'input EIR' : {'start_day' : 0,
                              'EIRs' : [1, 1, 1, 1, 1, 7, 8, 9, 5, 4, 6, 1]},
               'health seeking' : {'start_day' : 0,
                                   'drugs' : ['Artemether', 'Lumefantrine'],
                                   'trigger': 'NewClinicalCase',
                                   'coverage': 0.8, 
                                   'seek': 0.6, 
                                   'rate': 0.2 },
               'summary report' : { 'start_day' : 1,
                                    'interval' : 30.42,
                                    'number_reports' : 2000,
                                    'agebins' : [1000],
                                    'description': 'Monthly_Report'}},

    'Namawala' : { 'input EIR' : {'start_day' : 0,
                                  'EIRs' : [43.8, 68.5, 27.4, 46.6, 49.4, 24.7, 13.7, 11, 11, 2.74, 13.7, 16.5]},
                   'summary report' : { 'start_day' : 1,
                                        'interval' : 365,
                                        'number_reports' : 2000,
                                        'agebins' : [1000],
                                        'description': 'Annual_Report'}},

    'Dielmo' : { 'input EIR' : {'start_day' : 0,
                                  'EIRs' : [10.4, 13, 6, 2.6, 4, 6, 35, 21, 28, 15, 10.4, 8.4]},
                   'summary report' : { 'start_day' : 1,
                                        'interval' : 365,
                                        'number_reports' : 2000,
                                        'agebins' : [0.08333, 0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20, 25, 30, 40, 50, 60, 100],
                                        'description': 'Annual_Report'}},

    'Ndiop' : { 'input EIR' : {'start_day' : 0,
                                  'EIRs' : [0.39, 0.19, 0.77, 0, 0, 0, 6.4, 2.2, 4.7, 3.9, 0.87, 0.58]},
                   'summary report' : { 'start_day' : 1,
                                        'interval' : 365,
                                        'number_reports' : 2000,
                                        'agebins' : [0.08333, 0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20, 25, 30, 40, 50, 60, 100],
                                        'description': 'Annual_Report'}},

    'Sugungum' : { 'input EIR' : {'start_day' : 0,
                                  'EIRs' : [2.27,  6.83, 12.60, 20.23, 27.66, 26.89, 20.60, 
                                            10.31,  2.56,  0.50,  0.54,  1.01]},
                   'summary report' : { 'start_day' : 1,
                                        'interval' : 365,
                                        'number_reports' : 2000,
                                        'agebins' : [1000],
                                        'description': 'Annual_Report'}},

    'Matsari' : { 'input EIR' : {'start_day' : 0,
                                  'EIRs' : [1.17, 3.52, 6.49, 10.42, 14.25, 13.85, 10.61, 
                                            5.31, 1.32, 0.26, 0.28, 0.52]},
                  'summary report' : { 'start_day' : 1,
                                       'interval' : 365,
                                       'number_reports' : 2000,
                                       'agebins' : [1000],
                                       'description': 'Annual_Report'}},

    'Rafin_Marke' : { 'input EIR' : {'start_day' : 0,
                                  'EIRs' : [0.59, 1.11, 1.71, 2.55, 3.41, 3.37, 2.87, 
                                            1.95, 0.56, 0.12, 0.15, 0.31]},
                      'summary report' : { 'start_day' : 1,
                                           'interval' : 365,
                                           'number_reports' : 2000,
                                           'agebins' : [1000],
                                           'description': 'Annual_Report'}}
}


def set_geography_config(config, geography):
    mod_params = geographies_config[geography]
    config["parameters"].update(mod_params)
    return config

def set_geography_campaigns(cb, geography):
    campaigns = geographies_campaigns[geography]
    if 'input EIR' in campaigns.keys() :
        add_InputEIR(cb, campaigns['input EIR']['EIRs'], start_day=campaigns['input EIR']['start_day'])
    if 'summary report' in campaigns.keys() :
        add_summary_report(cb.campaign, start=campaigns['summary report']['start_day'], interval=campaigns['summary report']['interval'],
                           nreports=campaigns['summary report']['number_reports'], description=campaigns['summary report']['description'],
                           age_bins=campaigns['summary report']['agebins'])
    if 'health seeking' in campaigns.keys() :
        add_health_seeking(cb, start_day=campaigns['health seeking']['start_day'], drug=campaigns['health seeking']['drugs'], 
                           targets=[{'trigger' : 'NewClinicalCase', 'coverage' : campaigns['health seeking']['coverage'], 
                                     'seek' : campaigns['health seeking']['seek'], 'rate' : campaigns['health seeking']['rate']}])
        cb.update_params({'PKPD_Model' : 'CONCENTRATION_VERSUS_TIME'})
    if 'challenge bite' in campaigns.keys() :
        add_challenge_trial(cb)
    if 'survey' in campaigns.keys() :
        add_survey(cb.campaign, campaigns['survey']['survey_days'], reporting_interval=campaigns['survey']['interval'], 
                   nreports=campaigns['survey']['number_reports'], coverage=campaigns['survey']['number_reports'])

    return cb

def get_config_and_campaign_settings(geography) :
    return geographies_config[geography], geographies_campaigns[geography]