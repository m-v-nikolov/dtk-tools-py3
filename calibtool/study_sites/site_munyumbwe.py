from site_setup_functions import *

burn_years = 37
sim_duration = burn_years*365 + 3*365

itn_dates = [x/12. for x in [96, 36, 24, 12, 6, 3]]
itn_dates_2012 = [365*(burn_years-date)+165 for date in itn_dates]
itn_fracs_2012 = [0.098, 0.005, 0.071, 0.23, 0.57, 0.029]
itn_dates = [x/12. for x in [12, 6, 3]]
itn_dates_2013 = [365*(burn_years+1-date)+165 for date in itn_dates]
itn_fracs_2013 = [0.72, 0.25, 0.033]

irs_dates = [x/12. for x in 24, 12, 6, 3]
irs_dates_2012 = [365*(burn_years-date)+165 for date in irs_dates]
irs_fracs_2012 = [0.025, 0.226, 0.696, 0.053]
irs_dates = [x/12. for x in 12, 6, 3]
irs_dates_2013 = [365*(burn_years+1-date)+165 for date in irs_dates]
irs_fracs_2013 = [0.26, 0.705, 0.035]

round_days = [365*burn_years + x*60 +165 for x in range(3)] + [365*(burn_years + 1) + x*60 +165 for x in range(3)]

setup_functions = [ config_setup_fn(duration=sim_duration) ,
                    larval_habitat_fn(species="arabiensis", habitats=[1.08e10, 1.18e9]),
                    species_param_fn(species='arabiensis', param='Larval_Habitat_Types', value={ "TEMPORARY_RAINFALL": 1e10, "CONSTANT": 2e6 }),
                    species_param_fn(species="arabiensis", param="Indoor_Feeding_Fraction", value=0.5),
                    species_param_fn(species='funestus', param='Larval_Habitat_Types', value={ "PIECEWISE_MONTHLY": 1e10, "WATER_VEGETATION": 2e6 }),
                    summary_report_fn(start=365*burn_years+165,interval=1,nreports=1,age_bins=[5, 10, 15, 30, 200],description='Daily_Report', nodes={'Node_List' : range(1513), "class": "NodeSetNodeList"}),
                    filtered_report_fn(start=365*burn_years, end=sim_duration, nodes=range(1513)),
                    add_itn_by_node_id_fn('C:/Users/jgerardin/work/households_as_nodes/munyumbwe_all_hs_itn_cov.json', itn_dates_2012, itn_fracs_2012, 'itn2012cov'),
                    add_itn_by_node_id_fn('C:/Users/jgerardin/work/households_as_nodes/munyumbwe_all_hs_itn_cov.json', itn_dates_2013, itn_fracs_2013, 'itn2013cov'),
                    add_node_level_irs_by_node_id_fn('C:/Users/jgerardin/work/households_as_nodes/munyumbwe_all_hs_itn_cov.json', irs_dates_2012, irs_fracs_2012, 'irs2012cov'),
                    add_node_level_irs_by_node_id_fn('C:/Users/jgerardin/work/households_as_nodes/munyumbwe_all_hs_itn_cov.json', irs_dates_2013, irs_fracs_2013, 'irs2013cov'),
                    add_HS_by_node_id_fn('C:/Users/jgerardin/work/households_as_nodes/munyumbwe_all_hs_itn_cov.json', start=max([0,(burn_years-5)*365])),
                    add_drug_campaign_fn('MSAT_AL', [365*burn_years+165], coverage=0.5, repetitions=3, nodes={'Node_List' : range(1513), "class": "NodeSetNodeList"}),
                    add_drug_campaign_fn('MSAT_AL', [365*(burn_years+1)+165], coverage=0.63, repetitions=3, nodes={'Node_List' : range(1513), "class": "NodeSetNodeList"}),
                    #add_outbreak_fn(start_day=0, outbreak_fraction=0.2, tsteps_btwn=365, nodes={'Node_List' : [105, 95, 23, 38, 41, 45, 127], "class": "NodeSetNodeList"}),
                    #add_migration_fn(10001, start_day=130, coverage=0.5, repetitions=sim_duration/365+1, duration_of_stay=60, target={'agemin' : 15, 'agemax' : 30}),
                    input_eir_fn([3]*12, nodes={'Node_List' : [10001], "class": "NodeSetNodeList"}),
                    lambda cb : cb.update_params( { "Geography": "Household",
                                                    "Listed_Events": ["VaccinateNeighbors", "Blackout", "Distributing_AntimalariaDrug", 'TestedPositive', 'Give_Drugs', 
                                                                      'Received_Campaign_Drugs', 'Received_Treatment', 'Received_ITN', 'Received_Test'],
                                                    "Air_Temperature_Filename":   "Household/Munyumbwe_all_air_temperature_daily.bin",
                                                    "Land_Temperature_Filename":  "Household/Munyumbwe_all_air_temperature_daily.bin",
                                                    "Rainfall_Filename":          "Household/Munyumbwe_all3_rainfall_daily.bin", 
                                                    "Relative_Humidity_Filename": "Household/Munyumbwe_all_relative_humidity_daily.bin",
                                                    "Local_Migration_Filename":   "Household/Munyumbwe_Local_Migration.bin",
                                                    "Regional_Migration_Filename":"Household/Munyumbwe_Regional_Migration.bin",
                                                    "Sea_Migration_Filename":     "Household/Munyumbwe_Work_Migration.bin",
                                                    "Vector_Migration_Filename_Local":   "Household/Munyumbwe_Local_Vector_Migration.bin",
                                                    "Vector_Migration_Filename_Regional":   "Household/Munyumbwe_Regional_Vector_Migration.bin",
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
                                                    "Demographics_Filenames": ["Household/Munyumbwe_households_all_demographics_unif_fixedBR_work.json"],
                                                    "x_Temporary_Larval_Habitat" : 0.01,
                                                    "Enable_Spatial_Output" : 1,
                                                    "Spatial_Output_Channels" : ["Daily_EIR", "Population", 'New_Diagnostic_Prevalence'],
                                                    "Vector_Species_Names" : ['arabiensis', 'funestus'],
                                                    "Enable_Migration_Heterogeneity": 1, 
                                                    "Migration_Model": "FIXED_RATE_MIGRATION", 
                                                    #"Migration_Model": "NO_MIGRATION", 
                                                    "Enable_Local_Migration": 1,
                                                    "Local_Migration_Filename": "Household/Bbondo_households_Local_Migration.bin",
                                                    "Migration_Pattern": "SINGLE_ROUND_TRIPS",
                                                    "Local_Migration_Roundtrip_Duration"       : 3.0,
                                                    "Local_Migration_Roundtrip_Probability"    : 1.0,
                                                    "x_Local_Migration" : 0.1,
                                                    "Enable_Sea_Migration": 1,
                                                    "x_Sea_Migration" : 0.15,
                                                    "Sea_Migration_Filename": "Household/Bbondo_households_Work_Migration.bin",
                                                    "Sea_Migration_Roundtrip_Duration"         : 30.0,
                                                    "Sea_Migration_Roundtrip_Probability"      : 1.0
                                                    } )]

with open('C:/Users/jgerardin/work/households_as_nodes/munyumbwe_subsections.json') as fin :
    subset = json.loads(fin.read())
for key in subset :
    setup_functions.append(filtered_report_fn(start=365*burn_years, end=sim_duration, nodes=subset[key], description=key))

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
	                "prevalence_by_round" :
	                { 
	                  "all" : [0.2716, 0.1065, 0.0746, 0.1621, 0.0506, 0.03],
                      "SWvalley" : [0.589, 0.296, 0.242, 0.562, 0.170, 0.098],
                      "NEroad" : [0.431, 0.144, 0.072, 0.222, 0.058, 0.031],
                      "lowTarea" : [0.152, 0.051, 0.032, 0.057, 0.017, 0.013]
	                }
                }

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
                                              'testdays' : [365*burn_years+165],
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
                                        }
    }

def get_setup_functions() :

    return setup_functions

def load_reference_data(datatype) :

    return reference_data[datatype]

def get_analyzers(analyzer) :

    return analyzers[analyzer]

