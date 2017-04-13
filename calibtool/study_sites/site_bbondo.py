from site_setup_functions import *

burn_years = 50
sim_duration = burn_years*365 + 2*365

msat_day = 165
msat_offset = 20

itn_dates = [x/12. for x in [96, 36, 24, 12, 6, 3, 0]]
itn_dates_2012 = [365*(burn_years-date)+msat_day for date in itn_dates]
itn_fracs_2012 = [0.035, 0.047, 0.033, 0.42, 0.17, 0.29]

itn_dates = [x/12. for x in [12, 6, 3, 4]] # to give duration -1 for last birth-triggered distr
itn_dates_2013 = [365*(burn_years+1-date)+msat_day for date in itn_dates]
itn_fracs_2013 = [0.65, 0.2, 0.15]

days_in_month = [0, 31, 59, 214, 61]
hs_scale_by_month = [0.6, 0.9, 1, 0.8]

round_days = [365*(burn_years-1) + 355 - msat_offset] + [365*burn_years + x*60 +msat_day - msat_offset for x in range(3)] + [365*(burn_years + 1) + x*60 +msat_day - msat_offset for x in range(3)]

setup_functions = [ config_setup_fn(duration=sim_duration) ,
                    species_param_fn(species='arabiensis', param='Larval_Habitat_Types',
                                     value={"TEMPORARY_RAINFALL": 1e10,
                                            "CONSTANT": 2e6
                                            }),
                    #species_param_fn(species='arabiensis', param='Larval_Habitat_Types',
                    #                 value={ "TEMPORARY_RAINFALL": 1e10,
                    #                         "CONSTANT": 2e6,
                    #                         "LINEAR_SPLINE": {
                    #                             "Capacity_Distribution_Per_Year": {
                    #                                 "Times": [0.0, 30.417, 60.833, 91.25, 121.667, 152.083,
                    #                                           182.5, 212.917, 243.333, 273.75, 304.167, 334.583],
                    #                                 "Values": [0.2, 0.1, 0.0, 0.0, 0.0, 0.0,
                    #                                            0.0, 0.1, 0.1, 0.3, 0.3, 0.3]
                    #                             },
                    #                             "Max_Larval_Capacity": 1e10
                    #                         }
                    #                         }),
                    species_param_fn(species="arabiensis", param="Indoor_Feeding_Fraction", value=0.5),
                    species_param_fn(species='funestus', param='Larval_Habitat_Types',
                                     value={ "LINEAR_SPLINE": {
                                                "Capacity_Distribution_Per_Year": {
                                                    "Times":  [  0.0,  30.417,  60.833, 91.25, 121.667, 152.083,
                                                                 182.5, 212.917, 243.333, 273.75, 304.167, 334.583 ],
                                                    "Values": [  0.2,   0.5,     1.5,     1.0,
                                                                 1.0,     1.0,     0.5,   0.5,     0.3,     0.2,
                                                                 0.1, 0.1 ]
                                                },
                                                "Max_Larval_Capacity": 3e10
                                                            },
                                             "CONSTANT": 2e6,
                                             "WATER_VEGETATION": 2e6}),
                    filtered_report_fn(start=365*(burn_years-1), end=sim_duration, nodes=range(745)),
                    filtered_report_fn(start=365*(burn_years-1), end=sim_duration, nodes=[1001], description='worknode'),
                    add_itn_by_node_id_fn('C:/Users/jgerardin/work/households_as_nodes/bbondo_filled_all_hs_itn_cov.json', itn_dates_2012, itn_fracs_2012, 'itn2012cov',
                                          waning = {'Usage_Config': {"Expected_Discard_Time": 270}}),
                    add_itn_by_node_id_fn('C:/Users/jgerardin/work/households_as_nodes/bbondo_filled_all_hs_itn_cov.json', itn_dates_2013, itn_fracs_2013, 'itn2013cov',
                                          waning={'Usage_Config' : {"Expected_Discard_Time": 270}}),
                    #add_HS_by_node_id_fn('C:/Users/jgerardin/work/households_as_nodes/bbondo_filled_all_hs_itn_cov.json', start=max([0,(burn_years-5)*365])),
                    add_seasonal_HS_by_node_id_fn('C:/Users/jgerardin/work/households_as_nodes/bbondo_filled_all_hs_itn_cov.json',
                                                  days_in_month, hs_scale_by_month, start=max([0,(burn_years-5)*365])),

                    add_drug_campaign_fn('MSAT', 'AL',
                                         [365 * (burn_years + x) + msat_day - msat_offset for x in range(2)],
                                         repetitions=3, interval=60, coverage=0.6, delay=msat_offset, nodes=[1001]),
                    add_treatment_fn(start=365 * (burn_years - 5),
                                     targets=[{'trigger': 'NewClinicalCase', 'coverage': 1, 'agemin': 15, 'agemax': 200,
                                               'seek': 0.3, 'rate': 0.3},
                                              {'trigger': 'NewClinicalCase', 'coverage': 1, 'agemin': 0, 'agemax': 15,
                                               'seek': 0.45, 'rate': 0.3},
                                              {'trigger': 'NewSevereCase', 'coverage': 1, 'seek': 0.8, 'rate': 0.5}],
                                     nodes={'Node_List': [1001], "class": "NodeSetNodeList"}),

                    #add_drug_campaign_fn('MDA', 'DP', [0], repetitions=3, interval=20, coverage=1),


                    add_drug_campaign_fn('MSAT', 'AL',
                                         [365 * (burn_years - 1) + 355 - msat_offset],
                                         repetitions=1, coverage=0.3, delay=msat_offset, nodes=range(745)),

                    add_drug_campaign_fn('MSAT', 'AL', [365*burn_years+msat_day-msat_offset],  delay=msat_offset,
                                         coverage=0.6, repetitions=3, nodes=range(745)),
                    add_drug_campaign_fn('MSAT', 'AL', [365*(burn_years+1)+msat_day-msat_offset],  delay=msat_offset,
                                         coverage=0.6, repetitions=3, nodes=range(745)),
                    lambda cb : cb.update_params( { "Geography": "Household",
                                                    "Listed_Events": [ "VaccinateNeighbors", "Blackout", "Distributing_AntimalariaDrug", 'TestedPositive', 'Give_Drugs', 
                                                                       'IRS_Blackout', 'Node_Sprayed',  'Spray_IRS', 'Received_Campaign_Drugs', 'Received_Treatment', 
                                                                       'Received_ITN', 'Received_Test', 'Received_RCD_Drugs'],
                                                    "Air_Temperature_Filename":   "Household/Bbondo_filled_climate/const_temp/Bbondo_const_temp_air_temperature_daily.bin",
                                                    "Land_Temperature_Filename":  "Household/Bbondo_filled_climate/const_temp/Bbondo_const_temp_air_temperature_daily.bin",
                                                    "Rainfall_Filename":          "Household/Bbondo_filled_climate/const_temp/Bbondo_const_temp_rainfall_daily.bin",
                                                    "Relative_Humidity_Filename": "Household/Bbondo_filled_climate/const_temp/Bbondo_const_temp_humidity_daily.bin",
                                                    #"Air_Temperature_Filename": "Household/Bbondo_filled_climate/Bbondo_households_CBfilled_noworkvector_air_temperature_daily.bin",
                                                    #"Land_Temperature_Filename": "Household/Bbondo_filled_climate/Bbondo_households_CBfilled_noworkvector_air_temperature_daily.bin",
                                                    #"Rainfall_Filename": "Household/Bbondo_filled_climate/Bbondo_households_CBfilled_noworkvector_rainfall_daily.bin",
                                                    #"Relative_Humidity_Filename": "Household/Bbondo_filled_climate/Bbondo_households_CBfilled_noworkvector_humidity_daily.bin",

                                                    "Local_Migration_Filename": "Household/Bbondo_filled_Local_Migration.bin",
                                                    "Sea_Migration_Filename":     "Household/Bbondo_filled_Work_Migration.bin",
                                                    "Vector_Migration_Filename_Local":   "Household/Bbondo_filled_Local_Vector_Migration.bin",
                                                    "Vector_Migration_Filename_Regional":   "Household/Bbondo_filled_Regional_Vector_Migration.bin",
                                                    "Enable_Climate_Stochasticity": 0, # daily in raw data series
                                                    'Enable_Nondisease_Mortality' : 1,
                                                    "Vector_Sampling_Type": "TRACK_ALL_VECTORS",
                                                    "Enable_Vector_Aging": 1, 
                                                    "Enable_Vector_Mortality": 1,
                                                    "Birth_Rate_Dependence" : "FIXED_BIRTH_RATE",
                                                    "Enable_Demographics_Other": 0,
                                                    "Enable_Demographics_Initial": 1,
                                                    "Enable_Vital_Dynamics" : 1,
                                                    "Enable_Vector_Migration": 1, ##################################################################################################
                                                    "Enable_Vector_Migration_Local": 1, 
                                                    "Enable_Vector_Migration_Regional" : 1,
                                                    "Vector_Migration_Modifier_Equation" : "EXPONENTIAL",
                                                    "x_Vector_Migration_Local" : 100,
                                                    "x_Vector_Migration_Regional" : 0.1,
                                                    "Vector_Migration_Habitat_Modifier": 3.8, 
                                                    "Vector_Migration_Food_Modifier" : 0,
                                                    "Vector_Migration_Stay_Put_Modifier" : 10,
                                                    #"Demographics_Filenames": ["Household/Bbondo_households_all_demographics_unif_fixedBR_work.json"],
                                                    #"x_Temporary_Larval_Habitat" : 0.1,
                                                    "Enable_Spatial_Output" : 1,
                                                    "Spatial_Output_Channels" : ["Population", 'New_Diagnostic_Prevalence'],
                                                    "Enable_Default_Reporting" : 0,
                                                    "Vector_Species_Names" : ['arabiensis', 'funestus'],
                                                    "logLevel_SimulationEventContext": "ERROR",
                                                    "logLevel_VectorHabitat" : "ERROR",
                                                    "logLevel_NodeVector" : "ERROR",
                                                    "logLevel_JsonConfigurable" : "ERROR",
                                                    "logLevel_MosquitoRelease" : "ERROR",
                                                    "logLevel_VectorPopulationIndividual" : "ERROR",
                                                    "logLevel_LarvalHabitatMultiplier" : "ERROR",
                                                    "logLevel_StandardEventCoordinator": "ERROR",
                                                    'logLevel_NodeLevelHealthTriggeredIV' : 'ERROR',
                                                    'logLevel_NodeEventContext' : 'ERROR',
                                                    "Enable_Migration_Heterogeneity": 1,
                                                    "Migration_Model": "FIXED_RATE_MIGRATION", 
                                                    #"Migration_Model": "NO_MIGRATION", 
                                                    "Enable_Local_Migration": 1,
                                                    "Enable_Regional_Migration": 0,
                                                    "Migration_Pattern": "SINGLE_ROUND_TRIPS",
                                                    "Local_Migration_Roundtrip_Duration"       : 3.0,
                                                    "Local_Migration_Roundtrip_Probability"    : 1.0,
                                                    "x_Local_Migration" : 0.1,
                                                    "Enable_Sea_Migration": 1,
                                                    "x_Sea_Migration" : 0.15,
                                                    "Sea_Migration_Roundtrip_Duration"         : 30.0,
                                                    "Sea_Migration_Roundtrip_Probability"      : 1.0
                                                    } )]

reference_data = {  "risk_by_distance" :
	                { "distances" : [0, 0.05, 0.2],
	                  "prevalence" : 0.09166,
	                  "risks" : [0.15745, 0.12913, 0.10458]
	                },
                    # 75 household subset
	                #{ "distances" : [0, 0.05, 0.2],
	                #  "prevalence" : 0.1694,
	                #  "risks" : [0.22356, 0.28846, 0.14404]
	                #},
	                "prevalence_by_round" :
	                {
	                  "all" : [0.0825, 0.092, 0.022, 0.01, 0.035, 0.0077, 0.0052],
	                  "Test" : [0.092, 0.022, 0.01, 0.035, 0.0077, 0.0052],
	                },
	                "prevalence_by_age" :
                    # 75 household subset
	                #{ "age_bins" : [5, 10, 15, 30, 200],
	                #"RDT PfPR by Age Bin" : [0.16666666666666666, 0.203125, 0.21666666666666667, 0.15730337078651685, 0.0967741935483871],
	                #"n_obs" : [78, 64, 60, 89, 93]
    	            #}
                    # all bbondo
	                { "age_bins" : [5, 10, 15, 30, 200],
	                "RDT PfPR by Age Bin" : [0.0877742946708464, 0.11507936507936507, 0.1267605633802817, 0.09142857142857143, 0.054878048780487805],
	                "n_obs" : [319, 252, 213, 350, 328]
    	            }
                }

analyzers = {    'bbondo_eir_analyzer' : { 'name' : 'bbondo_eir_analyzer',
                                              'reporter' : 'Spatial Report',
                                              'fields_to_get' : ['Daily_EIR'],
                                              'burn_in' : 10,
                                              'map_size' : 1.7
                                          },
    'household_prevalence_analyzer' : { 'name' : 'analyze_prevalence_by_node',
                                              'reporter' : 'Spatial Report',
                                              'fields_to_get' : ['New_Diagnostic_Prevalence', 'Population'],
                                              'testdays' : [365*burn_years+msat_day],
                                              'map_size' : 1.7,
                                              'LL_fn' : 'euclidean_distance'
                                            },
    'prevalence_by_age_analyzer' : { 'name' : 'analyze_prevalence_by_age_noncohort',
                                             'reporter' : 'Daily Summary Report',
                                             'fields_to_get' : ['RDT PfPR by Age Bin',
                                                                'Average Population by Age Bin'],
                                             'LL_fn' : 'beta_binomial'
                                          },
    'prevalence_risk_analyzer' : { 'name' : 'analyze_prevalence_risk',
                                              'reporter' : 'Spatial Report',
                                              'fields_to_get' : ['New_Diagnostic_Prevalence', 'Population'],
                                              'testdays' : [365*burn_years+msat_day],
                                              'map_size' : 8,
                                              'LL_fn' : 'euclidean_distance',
                                              'worknode' : [1001]
                                          },
    'prevalence_by_round_analyzer' : { 'name' : 'analyze_prevalence_by_round',
                                              'reporter' : 'Filtered Report',
                                              'fields_to_get' : ['New Diagnostic Prevalence'],
                                              'testdays' : [x - burn_years*365 for x in round_days],
                                              'LL_fn' : 'euclidean_distance'
                                          },
    'PrevalenceByRoundAnalyzer' : {   'testdays' : [x - (burn_years-1)*365 for x in round_days],
                                      'regions' : ['all']
                                          },
    'PositiveFractionByDistanceAnalyzer' : {   "distmat" : "C:/Users/jgerardin/work/households_as_nodes/bbondo_filled_distance_matrix.csv",
                                               "ignore_nodes" : range(296,745) + [1001],
                                               'testday' : 365*burn_years+msat_day-msat_offset,
                                                }
    }

def get_setup_functions() :

    return setup_functions

def load_reference_data(datatype) :

    return reference_data[datatype]

def get_analyzers(analyzer) :

    return analyzers[analyzer]

