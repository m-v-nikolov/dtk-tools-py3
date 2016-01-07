from site_setup_functions import *

sim_duration = 50*365
setup_functions = [ config_setup_fn(duration=sim_duration) ,
                    larval_habitat_fn(species="arabiensis", habitats=[2e7, 8e9]),
                    species_param_fn(species="arabiensis", param="Indoor_Feeding_Fraction", value=0.8),
                    summary_report_fn(start=sim_duration-199,interval=1,nreports=1,age_bins=[5, 10, 15, 30, 200],description='Daily_Report', nodes={'Node_List' : range(296), "class": "NodeSetNodeList"}),
                    add_itn_by_node_id_fn('C:/Users/jgerardin/work/households_as_nodes/bbondo_all.csv', start=sim_duration-365),
                    add_HS_by_node_id_fn('C:/Users/jgerardin/work/households_as_nodes/bbondo_all.csv', start=max([0,sim_duration-5*365])),
                    #add_outbreak_fn(start_day=0, outbreak_fraction=0.2, tsteps_btwn=365, nodes={'Node_List' : [105, 95, 23, 38, 41, 45, 127], "class": "NodeSetNodeList"}),
                    add_migration_fn(1001, start_day=130, coverage=0.5, repetitions=sim_duration/365+1, duration_of_stay=60, target={'agemin' : 15, 'agemax' : 30}),
                    input_eir_fn([15]*12, nodes={'Node_List' : [1001], "class": "NodeSetNodeList"}),
                    lambda cb : cb.update_params( { "Geography": "Household",
                                                    "Listed_Events": ["VaccinateNeighbors", "Blackout", "Distributing_AntimalariaDrug", 'TestedPositive', 'Give_Drugs', 
                                                                      'Received_Campaign_Drugs', 'Received_Treatment', 'Received_ITN'],
                                                    #"Air_Temperature_Filename":   "Household/Zambia_Zambia_30arcsec_air_temperature_daily.bin",
                                                    #"Land_Temperature_Filename":  "Household/Zambia_Zambia_30arcsec_air_temperature_daily.bin",
                                                    #"Rainfall_Filename":          "Household/Zambia_Zambia_30arcsec_rainfall_daily.bin", 
                                                    #"Relative_Humidity_Filename": "Household/Zambia_Zambia_30arcsec_relative_humidity_daily.bin",
                                                    "Air_Temperature_Filename":   "Household/Zambia_Gwembe_30arcsec_air_temperature_daily.bin",
                                                    "Land_Temperature_Filename":  "Household/Zambia_Gwembe_30arcsec_air_temperature_daily.bin",
                                                    "Rainfall_Filename":          "Household/Zambia_Gwembe_30arcsec_rainfall_daily.bin", 
                                                    "Relative_Humidity_Filename": "Household/Zambia_Gwembe_30arcsec_relative_humidity_daily.bin",
                                                    "Local_Migration_Filename":   "Household/Bbondo_households_Local_Migration.bin",
                                                    "Regional_Migration_Filename":"Household/Bbondo_households_Regional_Migration.bin",
                                                    "Sea_Migration_Filename":     "Household/Bbondo_households_Work_Migration.bin",
                                                    "Vector_Migration_Filename_Local":   "Household/Bbondo_households_Local_Vector_Migration.bin",
                                                    "Vector_Migration_Filename_Regional":   "Household/Bbondo_households_Regional_Vector_Migration.bin",
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
                                                    "Vector_Migration_Stay_Put_Modifier" : 1.1,
                                                    #"Demographics_Filenames": ["Household/Bbondo_households_demographics_unif_fixedBR.json"],
                                                    "Demographics_Filenames": ["Household/Bbondo_households_all_demographics_unif_fixedBR_work.json"],
                                                    "x_Temporary_Larval_Habitat" : 0.01,
                                                    "Enable_Spatial_Output" : 1,
                                                    "Spatial_Output_Channels" : ["Daily_EIR", "Population", 'New_Diagnostic_Prevalence'],

                                                    "Enable_Migration_Heterogeneity": 1, 
                                                    "Migration_Model": "FIXED_RATE_MIGRATION", 
                                                    "Enable_Local_Migration": 1,
                                                    "Local_Migration_Filename": "Household/Bbondo_households_Local_Migration.bin",
                                                    "Migration_Pattern": "SINGLE_ROUND_TRIPS",
                                                    "Local_Migration_Roundtrip_Duration"       : 3.0,
                                                    "Local_Migration_Roundtrip_Probability"    : 1.0,
                                                    "x_Local_Migration" : 0.1,
                                                    "Enable_Sea_Migration": 1,
                                                    "x_Sea_Migration" : 0.1,
                                                    "Sea_Migration_Filename": "Household/Bbondo_households_Work_Migration.bin",
                                                    "Sea_Migration_Roundtrip_Duration"         : 30.0,
                                                    "Sea_Migration_Roundtrip_Probability"      : 1.0
                                                    } )]

reference_data = {  "annual_eir" : 
                    {  "151": 1.0866545131634515, "150": 4.4587026054038681, "153": 19.414441314403557, "152": 1.2813828406871657, "179": 12.583676398847006, "210": 0.079234332265977286, "156": 2.9223413090530164, "195": 2.0289768161402355, "197": 0.28383445479346892, "127": 12.206496062608457, "265": 0.046595072333126056, "214": 0.04161177443366347, "60": 0.087163341443035405, "114": 1.2550219343550411, "258": 3.3135629988207627, "63": 0.055610239092612271, "64": 0.031401687419406563, "53": 0.032567795664141384, "161": 1.0980988248304406, "276": 6.1643497960189473, "69": 0.084483728633979488, "87": 1.6527467127497402, "171": 3.0216767346464288, "259": 0.94486674797494519, "25": 2.4698919544128519, "275": 2.2379582819442616, "22": 0.019454608362406672, "23": 2.7182248052175404, "44": 9.5401609662813467, "45": 10.810937507738169, "43": 0.029034317547617094, "105": 19.922886201461413, "41": 11.204573330255624, "182": 0.49345803859725867, "183": 0.63195461168691114, "206": 7.5730398728597725, "185": 0.032592236166680805, "281": 0.06458672831271231, "188": 0.02236126280513312, "96": 0.093229023848175524, "277": 0.13968719125396467, "147": 1.4099902529637445, "196": 1.254885000954084, "140": 3.3174347281837342, "141": 0.048068107710568769, "149": 6.1692650431856455, "263": 11.866290178976323, "244": 8.3117207820196288, "122": 2.2323968848131166, "240": 1.2032176888216477, "71": 4.5375127861748465, "70": 1.7371653225205359, "227": 5.7197265320266286, "103": 2.7090007271546459, "269": 0.11748244836569285, "224": 0.14282238729528854, "95": 6.2428334735420323, "94": 0.88254685265431809, "221": 2.5256379364402304, "58": 0.12485338397901792, "118": 1.4656664102226309, "270": 0.056018187798943041, "38": 17.931861197663125, "59": 0.0482720567884415, "14": 3.2426593046230674, "283": 1.3429853697496339, "19": 0.16885025192322528, "54": 0.052415188499220416, "247": 0.846035144430625, "35": 1.8069663382053041, "130": 0.93654895885315037, "107": 0.029565726214586613, "116": 0.028175404868100811, "48": 0.078293011415549549, "264": 0.043111606301980819, "110": 0.058122565995944751
                	},
	                "risk_by_distance" :
	                { "distances" : [0, 0.05, 0.2],
	                  "prevalence" : 0.09166,
	                  "risks" : [0.15296, 0.12913, 0.10458]
	                },
                    # 75 household subset
	                #{ "distances" : [0, 0.05, 0.2],
	                #  "prevalence" : 0.1694,
	                #  "risks" : [0.22356, 0.28846, 0.14404]
	                #},
	                "prevalence_by_node" :
	                {"151": 0.0, "150": 0.33333333333333331, "153": 0.33333333333333331, "152": 0.22222222222222221, "179": 1.0, "210": 0.0, "156": 0.20000000000000001, "195": 0.14285714285714285, "197": 0.14285714285714285, "127": 0.5, "265": 0.0, "214": 0.0, "60": 0.0, "114": 0.20000000000000001, "258": 0.16666666666666666, "63": 0.0, "64": 0.0, "53": 0.0, "161": 0.18181818181818182, "276": 0.25, "69": 0.0, "87": 0.16666666666666666, "171": 0.16666666666666666, "259": 0.25, "25": 0.14285714285714285, "275": 0.20000000000000001, "22": 0.0, "23": 0.5, "44": 1.0, "45": 0.5, "43": 0.0, "105": 0.83333333333333337, "41": 0.5, "182": 0.0, "183": 0.0, "206": 0.25, "185": 0.0, "281": 0.0, "188": 0.0, "96": 0.0, "277": 0.0, "147": 0.22222222222222221, "196": 0.25, "140": 0.0, "141": 0.0, "149": 0.20000000000000001, "263": 0.33333333333333331, "244": 0.33333333333333331, "122": 0.33333333333333331, "240": 0.0, "71": 0.25, "70": 0.0, "227": 0.33333333333333331, "103": 0.25, "269": 0.0, "224": 0.0, "95": 0.66666666666666663, "94": 0.0, "221": 0.0, "58": 0.0, "118": 0.0, "270": 0.0, "38": 0.5, "59": 0.0, "14": 0.25, "283": 0.16666666666666666, "19": 0.0, "54": 0.0, "247": 0.14285714285714285, "35": 0.14285714285714285, "130": 0.14285714285714285, "107": 0.0, "116": 0.0, "48": 0.0, "264": 0.0, "110": 0.0
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
                                              'testdays' : [-1*(365-166)],
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
                                              'testdays' : [-1*(365-166)],
                                              'map_size' : 8,
                                              'LL_fn' : 'euclidean_distance',
                                              'worknode' : [1001]
                                          }}

def get_setup_functions() :

    return setup_functions

def load_reference_data(datatype) :

    return reference_data[datatype]

def get_analyzers(analyzer) :

    return analyzers[analyzer]

