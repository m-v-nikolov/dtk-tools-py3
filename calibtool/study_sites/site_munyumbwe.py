from site_setup_functions import *
import pandas as pd

burn_years = 50
sim_duration = burn_years*365 + 2*365

itn_dates = [x/12. for x in [96, 36, 24, 12, 6, 3, 0]]
itn_dates_2012 = [365*(burn_years-date)+165 for date in itn_dates]
itn_fracs_2012 = [0.098, 0.005, 0.071, 0.23, 0.57, 0.029]
itn_dates = [x/12. for x in [12, 6, 3, 0]]
itn_dates_2013 = [365*(burn_years+1-date)+165 for date in itn_dates]
itn_fracs_2013 = [0.72, 0.25, 0.033]
itn_dates = [x/12. for x in [18, 12, 6, 3, 0]]
itn_dates_2014 = [365*(burn_years+2-date)+335 for date in itn_dates]
itn_fracs_2014 = [0.217, 0.327, 0.435, 0.026]


irs_dates = [x/12. for x in [24, 12, 6, 3]]
irs_dates_2012 = [365*(burn_years-date)+165 for date in irs_dates]
irs_fracs_2012 = [0.025, 0.226, 0.696, 0.053]
irs_dates = [x/12. for x in [12, 6, 3]]
irs_dates_2013 = [365*(burn_years+1-date)+165 for date in irs_dates]
irs_fracs_2013 = [0.26, 0.705, 0.035]
irs_dates = [x/12. for x in [24, 12, 6, 3]]
irs_dates_2014 = [365*(burn_years+2-date)+335 for date in irs_dates]
irs_fracs_2014 = [0.188, 0.193, 0.034, 0.585]

msat_day = 165
msat_offset = 20

days_in_month = [0, 31, 28, 31, 214, 30, 31]
scale_hs_by_month = [0.5, 0.3, 0.5, 1, 0.7, 0.6]

round_days = [365*(burn_years-1) + 355 - msat_offset] + [365*burn_years + x*60 +msat_day - msat_offset for x in range(3)] + [365*(burn_years + 1) + x*60 +msat_day - msat_offset for x in range(3)]

with open('C:/Users/jgerardin/work/households_as_nodes/munyumbwe_filled_subsections.json') as fin :
    subset = json.loads(fin.read())
subset['all'] = range(3152)

run_section = 'all'
coverage_fname = 'C:/Users/jgerardin/work/households_as_nodes/munyumbwe_filled_all_hs_itn_cov.json'

df = pd.read_csv('C:/Users/jgerardin/work/households_as_nodes/munyumbwe_filled_all.csv')
r1subset = df[~df['in_r1']]['ids'].values

setup_functions = [ config_setup_fn(duration=sim_duration) ,
                    set_params_by_species_fn(species=['arabiensis', 'funestus', 'munyumbwe_funestus']),
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
                    species_param_fn(species='munyumbwe_funestus', param='Larval_Habitat_Types',
                                     value={ "LINEAR_SPLINE": {
                                                "Capacity_Distribution_Per_Year": {
                                                    "Times":  [  0.0,  30.417,  60.833, 91.25, 121.667, 152.083,
                                                                 182.5, 212.917, 243.333, 273.75, 304.167, 334.583 ],
                                                    "Values": [  0.5,   0.5,     0.3,     0.1,
                                                                 0.002,     0.002,     0.002,   0.3,     0.5,     1.0,
                                                                 1.0, 0.5 ]
                                                },
                                                "Max_Larval_Capacity": 3e10
                                                            },
                                             "CONSTANT": 2e6,
                                             "WATER_VEGETATION": 2e6}),
                    #summary_report_fn(start=365*burn_years+msat_day,interval=1,nreports=1,age_bins=[5, 10, 15, 30, 200],description='Daily_Report', nodes={'Node_List' : subset[run_section], "class": "NodeSetNodeList"}),
                    filtered_report_fn(start=365*(burn_years-1), end=sim_duration, nodes=subset[run_section]),
                    filtered_report_fn(start=365*(burn_years-1), end=sim_duration, nodes=[10001], description='worknode'),
                    add_itn_by_node_id_fn(coverage_fname, itn_dates_2012, itn_fracs_2012, 'itn2012cov', waning={'Usage_Config' : {"Expected_Discard_Time": 270}}),
                    add_itn_by_node_id_fn(coverage_fname, itn_dates_2013, itn_fracs_2013, 'itn2013cov', waning={'Usage_Config' : {"Expected_Discard_Time": 270}}),
                    add_itn_by_node_id_fn(coverage_fname, itn_dates_2014, itn_fracs_2014, 'itn2014cov', waning={'Usage_Config' : {"Expected_Discard_Time": 270}}),
                    add_node_level_irs_by_node_id_fn(coverage_fname, irs_dates_2012, irs_fracs_2012, 'irs2012cov'),
                    add_node_level_irs_by_node_id_fn(coverage_fname, irs_dates_2013, irs_fracs_2013, 'irs2013cov'),
                    add_node_level_irs_by_node_id_fn(coverage_fname, irs_dates_2014, irs_fracs_2014, 'irs2014r1cov',
                                                     initial_killing=0.6, box_duration=365),
                    #add_HS_by_node_id_fn(coverage_fname, start=max([0,(burn_years-5)*365])),
                    add_seasonal_HS_by_node_id_fn(coverage_fname, days_in_month, scale_hs_by_month, start=max([0,(burn_years-5)*365])),


                    #add_drug_campaign_fn('MDA', 'DP', [0], repetitions=3, interval=20, coverage=1),

                    add_drug_campaign_fn('MSAT', 'AL', [365*(burn_years+x)+msat_day-msat_offset for x in range(2)],
                                         repetitions=3, interval=60, coverage=0.6, delay=msat_offset, nodes=[10001]),
                    add_treatment_fn(start=365*(burn_years-5),
                                     targets=[ { 'trigger': 'NewClinicalCase', 'coverage': 1, 'agemin':15, 'agemax':200, 'seek': 0.3, 'rate': 0.3 },
                                               { 'trigger': 'NewClinicalCase', 'coverage': 1, 'agemin':0, 'agemax':15, 'seek':  0.45, 'rate': 0.3 },
                                               { 'trigger': 'NewSevereCase',   'coverage': 1, 'seek': 0.8, 'rate': 0.5 } ],
                                     nodes={'Node_List' : [10001], "class": "NodeSetNodeList"}),
                    add_drug_campaign_fn('MSAT', 'AL',
                                         [365 * (burn_years - 1) + 355 - msat_offset],
                                         repetitions=1, coverage=0.4, delay=msat_offset, nodes=subset['all']),
                    add_drug_campaign_fn('MSAT', 'AL',
                                         [365 * (burn_years + x) + msat_day - msat_offset for x in range(2)],
                                         repetitions=3, interval=60, coverage=0.6, delay=msat_offset, nodes=subset['all']),

                    #input_eir_fn([3]*12, nodes={'Node_List' : [10001], "class": "NodeSetNodeList"}),
                    lambda cb : cb.update_params( { "Geography": "Household",
                                                    "Listed_Events": [ "VaccinateNeighbors", "Blackout", "Distributing_AntimalariaDrug", 'TestedPositive', 'Give_Drugs',
                                                                       'IRS_Blackout', 'Node_Sprayed',  'Spray_IRS', 'Received_Campaign_Drugs', 'Received_Treatment',
                                                                       'Received_ITN', 'Received_Test', 'Received_RCD_Drugs'],
                                                    #"Air_Temperature_Filename":   "Household/Munyumbwe_filled/Zambia_Mumyumbwe_all_map2cellCSV3_2.5arcmin_air_temperature_daily.bin",
                                                    #"Land_Temperature_Filename":  "Household/Munyumbwe_filled/Zambia_Mumyumbwe_all_map2cellCSV3_2.5arcmin_air_temperature_daily.bin",
                                                    #"Rainfall_Filename":          "Household/Munyumbwe_filled/Zambia_Mumyumbwe_all_map2cell_2.5arcmin_rainfall_daily.bin",
                                                    #"Relative_Humidity_Filename": "Household/Munyumbwe_filled/Zambia_Mumyumbwe_all_map2cell_2.5arcmin_relative_humidity_daily.bin",
                                                    "Air_Temperature_Filename": "Household/Munyumbwe_filled/const_temp/Munyumbwe_filled_air_temperature_daily.bin",
                                                    "Land_Temperature_Filename": "Household/Munyumbwe_filled/const_temp/Munyumbwe_filled_air_temperature_daily.bin",
                                                    "Rainfall_Filename": "Household/Munyumbwe_filled/const_temp/Munyumbwe_filled_rainfall_daily.bin",
                                                    "Relative_Humidity_Filename": "Household/Munyumbwe_filled/const_temp/Munyumbwe_filled_humidity_daily.bin",

                                                    "Local_Migration_Filename":   "Household/Munyumbwe_filled/Munyumbwe_filled_%s_Local_Migration.bin" % run_section,
                                                    "Regional_Migration_Filename":"",
                                                    "Sea_Migration_Filename":     "Household/Munyumbwe_filled/Munyumbwe_filled_%s_Work_Migration.bin" % run_section,
                                                    "Vector_Migration_Filename_Local":   "Household/Munyumbwe_filled/Munyumbwe_filled_%s_Local_Vector_Migration.bin" % run_section,
                                                    "Vector_Migration_Filename_Regional":   "Household/Munyumbwe_filled/Munyumbwe_filled_%s_Regional_Vector_Migration.bin" % run_section,
                                                    "Enable_Climate_Stochasticity": 0, # daily in raw data series
                                                    'Enable_Nondisease_Mortality' : 1,
                                                    "Vector_Sampling_Type": "TRACK_ALL_VECTORS",
                                                    "Enable_Vector_Aging": 1,
                                                    "Enable_Vector_Mortality": 1,
                                                    "Birth_Rate_Dependence" : "FIXED_BIRTH_RATE",
                                                    "Enable_Demographics_Other": 0,
                                                    "Enable_Demographics_Initial": 1,
                                                    "Enable_Vital_Dynamics" : 1,
                                                    "Enable_Vector_Migration": 1,
                                                    "Enable_Vector_Migration_Local": 1,
                                                    "Enable_Vector_Migration_Regional" : 1,
                                                    "Vector_Migration_Modifier_Equation" : "EXPONENTIAL",
                                                    "x_Vector_Migration_Local" : 100,
                                                    "x_Vector_Migration_Regional" : 0.1,
                                                    "Vector_Migration_Habitat_Modifier": 3.8,
                                                    "Vector_Migration_Food_Modifier" : 0,
                                                    "Vector_Migration_Stay_Put_Modifier" : 10,
                                                    "Demographics_Filenames": ["Household/Munyumbwe_households_all_demographics_MN.json"],
                                                    #"x_Temporary_Larval_Habitat" : 0.03,
                                                    "Enable_Spatial_Output" : 1,
                                                    "Spatial_Output_Channels" : ["Population", 'New_Diagnostic_Prevalence'],
                                                    "Enable_Default_Reporting": 0,
                                                    "Vector_Species_Names" : ['arabiensis', 'funestus', 'munyumbwe_funestus'],
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
                                                    'logLevel_NodeEventCoordinator' : 'ERROR',
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
    #setup_functions.append(filtered_report_fn(start=365*burn_years, end=sim_duration,
    #                                          nodes=[x for x in subset[key] if x in df[df['in_r1']]['ids'].values],
    #                                          description=key))
    setup_functions.append(filtered_report_fn(start=365 * (burn_years-1), end=sim_duration,
                                              nodes=subset[key],
                                              description=key))

#setup_functions.append(filtered_report_fn(start=365*(burn_years-5), end=sim_duration, nodes=subset[run_section], description=run_section))


for date in range(4) :
    setup_functions.append(add_mosquito_release_fn(0+10*date, 'arabiensis', 1,
                                                   nodes={'Node_List' : subset['lowTarea'], "class": "NodeSetNodeList"}))
    setup_functions.append(add_mosquito_release_fn(0+10*date, 'arabiensis', 10,
                                                   nodes={'Node_List' : subset['NEroad'], "class": "NodeSetNodeList"}))
    setup_functions.append(add_mosquito_release_fn(msat_day - msat_offset - 10*date, 'funestus', 10,
                                                   nodes={'Node_List' : subset['SWvalley'], "class": "NodeSetNodeList"}))
    setup_functions.append(add_mosquito_release_fn(msat_day - msat_offset - 10 * date, 'funestus', 100,
                                                   nodes={'Node_List': subset['Sompani'], "class": "NodeSetNodeList"}))

df = pd.read_csv('C:/Users/jgerardin/work/households_as_nodes/munyumbwe_filled_all.csv')
mg = pd.read_csv('C:/Users/jgerardin/work/households_as_nodes/munyumbwe_migration_matrix_outside_by_round_for_dtk.csv')
mg_scale = 0.01

for i, row in mg.iterrows() :
    setup_functions.append(add_migration_fn(10001, start_day=row['from_date'], coverage=mg_scale*row['from_highT_rate'],
                                            repetitions=sim_duration/365,
                                            duration_at_node_distr_type='POISSON_DURATION',
                                            duration_of_stay=60,
                                            duration_before_leaving_distr_type='POISSON_DURATION',
                                            duration_before_leaving=10,
                                            nodesfrom={'Node_List' : [int(x) for x in df[df['cluster'] == row['cluster.i']]['ids'].values],
                                                       "class": "NodeSetNodeList"}) )
    setup_functions.append(add_migration_fn(10001, start_day=row['to_date'], coverage=mg_scale * row['to_highT_rate'],
                                            repetitions=sim_duration / 365,
                                            duration_at_node_distr_type='POISSON_DURATION',
                                            duration_of_stay=60,
                                            duration_before_leaving_distr_type='POISSON_DURATION',
                                            duration_before_leaving=10,
                                            nodesfrom={'Node_List': [int(x) for x in df[df['cluster'] == row['cluster.i']]['ids'].values],
                                                       "class": "NodeSetNodeList"}) )


reference_data = {
                  # 802 hh
	                #"risk_by_distance" :
	                #{ "distances" : [0, 0.05, 0.2],
	                #  "prevalence" : 0.1576,
	                #  "risks" : [0.2595, 0.1698, 0.1807]
	                #},
	                #"prevalence_by_round" :
	                #{
	                #  "prevalence" : [0.158, 0.052, 0.0352, 0.0512, 0.0124, 0.0111]
	                #}
                  # all Munyumbwe
	                "risk_by_distance" :
	                { "distances" : [0, 0.05, 0.2],
	                  "prevalence" : 0.2716,
	                  "risks" : [0.5026, 0.3079, 0.325]
	                },
	                "prevalence_by_round" : # CB corrected
	                {
	                  "all" : [0.183, 0.25, 0.098, 0.071, 0.15, 0.048, 0.029],
                      #"SWvalley" : [0.54, 0.27, 0.22, 0.51, 0.17, 0.089], # original SWvalley
                      "SWvalley" : [0.444, 0.5, 0.22, 0.14, 0.48, 0.16, 0.074], # truncated SWvalley
                      "Sompani" : [0.5, 0.65, 0.44, 0.42, 0.6, 0.2, 0.14],
                      "NEroad" : [0.215, 0.4, 0.13, 0.071, 0.2, 0.055, 0.027],
                      "lowTarea" : [0.119, 0.14, 0.048, 0.031, 0.052, 0.016, 0.013]
	                }

                }

"""
"prevalence_by_round" : # uncorrected
{
	"all" : [0.2716, 0.1065, 0.0746, 0.1621, 0.0506, 0.03],
    "SWvalley" : [0.589, 0.296, 0.242, 0.562, 0.170, 0.098],
    "NEroad" : [0.431, 0.144, 0.072, 0.222, 0.058, 0.031],
    "lowTarea" : [0.152, 0.051, 0.032, 0.057, 0.017, 0.013]
},
"""


analyzers = {
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
                                              'map_size' : 20,
                                              'LL_fn' : 'euclidean_distance',
                                              'worknode' : [10001]
                                          },
    'prevalence_by_round_analyzer' : { 'name' : 'analyze_prevalence_by_round',
                                        'reporter' : 'Filtered Report',
                                        'fields_to_get' : ['New Diagnostic Prevalence'],
                                        'testdays' : [x - burn_years*365 for x in round_days],
                                        'LL_fn' : 'euclidean_distance',
                                        'regions' : subset.keys()
                                        },
    'PrevalenceByRoundAnalyzer' : {   'testdays' : [x - (burn_years-1)*365 for x in round_days],
                                      #'regions' : [run_section]
                                      'regions' : ['all', 'SWvalley', 'NEroad', 'lowTarea', 'Sompani']
                                          },
    'PositiveFractionByDistanceAnalyzer' : {   "distmat" : "C:/Users/jgerardin/work/households_as_nodes/munyumbwe_filled_all_r1_distance_matrix.csv",
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

