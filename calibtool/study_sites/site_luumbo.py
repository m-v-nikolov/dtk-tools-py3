from site_setup_functions import *
import pandas as pd

burn_years = 50
sim_duration = burn_years*365 + 2*365

itn_dates = [x/12. for x in [36, 24, 12, 6, 3, 0]]
itn_dates_2012 = [365*(burn_years-date)+165 for date in itn_dates]
itn_fracs_2012 = [0.03, 0.26, 0.17, 0.13, 0.4]

itn_dates = [x/12. for x in [12, 6, 3, 0]]
itn_dates_2013 = [365*(burn_years+1-date)+165 for date in itn_dates]
itn_fracs_2013 = [0.39, 0.14, 0.39]

itn_dates = [x/12. for x in [12, 6, 3, 0]]
itn_dates_2014 = [365*(burn_years+2-date)+335 for date in itn_dates]
itn_fracs_2014 = [0.44, 0.51, 0.03]

irs_dates = [x/12. for x in [12, 6, 3]]
irs_dates_2013 = [365*(burn_years+1-date)+165 for date in irs_dates]
irs_fracs_2013 = [0.04, 0.5, 0.46]

msat_day = 165
msat_offset = 20

days_in_month = [0, 31, 59, 214, 61]
scale_hs_by_month = [0.6, 0.9, 1, 0.8]

round_days = [365*burn_years + x*60 +msat_day - msat_offset for x in range(3)] + [365*(burn_years + 1) + x*60 +msat_day - msat_offset for x in range(3)]

with open('C:/Users/jgerardin/work/households_as_nodes/luumbo_filled_subsections.json') as fin :
    subset = json.loads(fin.read())
subset['all'] = range(744)

run_section = 'all'
coverage_fname = 'C:/Users/jgerardin/work/households_as_nodes/luumbo_filled_all_hs_itn_cov.json'

df = pd.read_csv('C:/Users/jgerardin/work/households_as_nodes/luumbo_filled_all.csv')
r1subset = df[~(df['in_r1'] == 1)]['ids'].values

setup_functions = [ config_setup_fn(duration=sim_duration) ,
                    species_param_fn(species='arabiensis', param='Larval_Habitat_Types',
                                     value={"TEMPORARY_RAINFALL": 1e10,
                                            "CONSTANT": 2e6
                                            }),
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
                    filtered_report_fn(start=365*(burn_years), end=sim_duration, nodes=subset[run_section]),
                    filtered_report_fn(start=365*(burn_years), end=sim_duration, nodes=[10001], description='worknode'),
                    add_itn_by_node_id_fn(coverage_fname, itn_dates_2012, itn_fracs_2012, 'itn2012cov', waning={'Usage_Config' : {"Expected_Discard_Time": 270}}),
                    add_itn_by_node_id_fn(coverage_fname, itn_dates_2013, itn_fracs_2013, 'itn2013cov', waning={'Usage_Config' : {"Expected_Discard_Time": 270}}),
                    add_itn_by_node_id_fn(coverage_fname, itn_dates_2014, itn_fracs_2014, 'itn2014cov', waning={'Usage_Config' : {"Expected_Discard_Time": 270}}),
                    add_node_level_irs_by_node_id_fn(coverage_fname, irs_dates_2013, irs_fracs_2013, 'irs2013cov'),

                    ##add_HS_by_node_id_fn(coverage_fname, start=max([0,(burn_years-5)*365])),
                    add_seasonal_HS_by_node_id_fn(coverage_fname, days_in_month, scale_hs_by_month, start=max([0,(burn_years-5)*365])),

                    add_drug_campaign_fn('MSAT', 'AL', [365*(burn_years+x)+msat_day-msat_offset for x in range(2)],
                                         repetitions=3, interval=60, coverage=0.6, delay=msat_offset, nodes=[10001]),
                    add_treatment_fn(start=365*(burn_years-5),
                                     targets=[ { 'trigger': 'NewClinicalCase', 'coverage': 1, 'agemin':15, 'agemax':200, 'seek': 0.3, 'rate': 0.3 },
                                               { 'trigger': 'NewClinicalCase', 'coverage': 1, 'agemin':0, 'agemax':15, 'seek':  0.45, 'rate': 0.3 },
                                               { 'trigger': 'NewSevereCase',   'coverage': 1, 'seek': 0.8, 'rate': 0.5 } ],
                                     nodes={'Node_List' : [10001], "class": "NodeSetNodeList"}),

                    add_drug_campaign_fn('MSAT', 'AL',
                                         [365 * (burn_years) + msat_day - msat_offset],
                                         repetitions=1, interval=60, coverage=0.2, delay=msat_offset, nodes=subset['all']),
                    add_drug_campaign_fn('MSAT', 'AL',
                                         [365 * (burn_years) + msat_day - msat_offset + 60],
                                         repetitions=2, interval=60, coverage=0.4, delay=msat_offset, nodes=subset['all']),
                    add_drug_campaign_fn('MSAT', 'AL',
                                         [365 * (burn_years + 1) + msat_day - msat_offset],
                                         repetitions=3, interval=60, coverage=0.4, delay=msat_offset,
                                         nodes=subset['all']),

                    lambda cb : cb.update_params( { "Geography": "Household",
                                                    "Listed_Events": [ "VaccinateNeighbors", "Blackout", "Distributing_AntimalariaDrug", 'TestedPositive', 'Give_Drugs', 
                                                                       'IRS_Blackout', 'Node_Sprayed',  'Spray_IRS', 'Received_Campaign_Drugs', 'Received_Treatment', 
                                                                       'Received_ITN', 'Received_Test', 'Received_RCD_Drugs'],
                                                    "Air_Temperature_Filename": "Household/Luumbo_filled/Luumbo_filled_air_temperature_daily.bin",
                                                    "Land_Temperature_Filename": "Household/Luumbo_filled/Luumbo_filled_air_temperature_daily.bin",
                                                    "Rainfall_Filename": "Household/Luumbo_filled/Luumbo_filled_rainfall_daily.bin",
                                                    "Relative_Humidity_Filename": "Household/Luumbo_filled/Luumbo_filled_humidity_daily.bin",
                                                    "Local_Migration_Filename": "Household/Luumbo_filled/Luumbo_Local_Migration.bin",
                                                   "Regional_Migration_Filename":"",
                                                    "Sea_Migration_Filename":     "Household/Luumbo_filled/Luumbo_Work_Migration.bin",
                                                    "Vector_Migration_Filename_Local":   "Household/Luumbo_filled/Luumbo_Local_Vector_Migration.bin",
                                                    "Vector_Migration_Filename_Regional":   "Household/Luumbo_filled/Luumbo_Regional_Vector_Migration.bin",
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
                                                    "Demographics_Filenames": ["Household/Luumbo_filled_demographics_all.json"],
                                                    #"x_Temporary_Larval_Habitat" : 0.03,
                                                    "Enable_Spatial_Output" : 1,
                                                    "Spatial_Output_Channels" : ["Population", 'New_Diagnostic_Prevalence'],
                                                    "Enable_Default_Reporting": 0,
                                                    "Vector_Species_Names" : ['arabiensis', 'funestus'],
                                                    "logLevel_SimulationEventContext": "ERROR",
                                                    "logLevel_VectorHabitat" : "ERROR",
                                                    "logLevel_NodeVector" : "ERROR",
                                                    "logLevel_JsonConfigurable" : "ERROR",
                                                    "logLevel_MosquitoRelease" : "ERROR",
                                                    "logLevel_VectorPopulationIndividual" : "ERROR",
                                                    "logLevel_LarvalHabitatMultiplier" : "ERROR",
                                                    "logLevel_StandardEventCoordinator" : "ERROR",
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

for key in subset :
    setup_functions.append(filtered_report_fn(start=365 * (burn_years), end=sim_duration,
                                              nodes=subset[key],
                                              description=key))

"""
for date in range(4) :
    setup_functions.append(add_mosquito_release_fn(msat_day - msat_offset - 10*date, 'funestus', 10,
                                                   nodes={'Node_List' : subset['NW'], "class": "NodeSetNodeList"}))
    setup_functions.append(add_mosquito_release_fn(msat_day - msat_offset - 10 * date, 'funestus', 100,
                                                   nodes={'Node_List': subset['SE'], "class": "NodeSetNodeList"}))

setup_functions.append(add_migration_fn(10001, start_day=300, coverage=0.01,
                                        repetitions=sim_duration / 365,
                                        duration_at_node_distr_type='POISSON_DURATION',
                                        duration_of_stay=60,
                                        duration_before_leaving_distr_type='POISSON_DURATION',
                                        duration_before_leaving=10,
                                        nodesfrom={'Node_List': subset['NW'],
                                                   "class": "NodeSetNodeList"}))
"""
#df = pd.read_csv('C:/Users/jgerardin/work/households_as_nodes/luumbo_filled_all.csv')

reference_data = {  
                  # all luumbo
	                "risk_by_distance" :
	                { "distances" : [0, 0.05, 0.2],
	                  "prevalence" : 0.392,
	                  "risks" : [0.635, 0.513, 0.429]
	                },                      
	                "prevalence_by_round" : # CB corrected
	                { 
	                  "all" : [0.392, 0.245, 0.181, 0.378, 0.207, 0.156],
                      "NW" : [0.141, 0.075, 0.063, 0.17, 0.051, 0.034],
                      "SE" : [0.566, 0.304, 0.223, 0.481, 0.276, 0.205]
	                }

                }

analyzers = {    
    'PrevalenceByRoundAnalyzer' : {   'testdays' : [x - (burn_years)*365 for x in round_days],
                                      'regions' : ['all', 'NW', 'SE']
                                          },
    'PositiveFractionByDistanceAnalyzer' : {   "distmat" : "C:/Users/jgerardin/work/households_as_nodes/luumbo_filled_all_r1_distance_matrix.csv",
                                               "ignore_nodes" : [10001] + r1subset,
                                               'testday' : 365*burn_years+msat_day-msat_offset,
                                                }
    }

def get_setup_functions() :

    return setup_functions

def load_reference_data(datatype) :

    return reference_data[datatype]

def get_analyzers(analyzer) :

    return analyzers[analyzer]

