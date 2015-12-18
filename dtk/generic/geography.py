import os

from dtk.generic.demographics import set_static_demographics

def convert_filepaths(params):
    """
    Make sure to add the geography folder in front of the paths.
    For example, if the geography is Namawala, we want the climate/demographics files to be Namawala\file.json

    :param params: The config parameters
    :return: Nothing
    """
    g = params.pop('Geography',None)
    if not g: return
    for k, v in params.items():
        if k == 'Demographics_Filename':
            params['Demographics_Filenames'] = [os.path.join(g, fn) for fn in params.pop(k).split(';')]
        elif k == 'Demographics_Filenames':
            params[k] = [os.path.join(g, fn) for fn in v]
        elif 'Filename' in k:
            params[k] = os.path.join(g, v)

def get_converted_paths_for_geography(geography):

    params = geographies.get(geography).copy()
    if not params:
        raise Exception('%s geography not yet implemented' % geography)
    convert_filepaths(params)
    return params

def get_geography_parameter(geography, param):
    geography = geography.split('.')[0] # e.g. Sinazongwe.static
    params = get_converted_paths_for_geography(geography)
    return params.get(param)

# Set climate and demographics files by geography
def set_geography(cb, geography, static=False, pop_scale=1):
    params = get_converted_paths_for_geography(geography)
    cb.update_params(params)
    if static:
        set_static_demographics(cb, use_existing=True)
    if pop_scale != 1:
        cb.set_param('Base_Population_Scale_Factor', pop_scale*cb.get_param('Base_Population_Scale_Factor'))
        if cb.get_param('Birth_Rate_Dependence') == 'FIXED_BIRTH_RATE':
            cb.set_param('x_Birth', pop_scale*cb.get_param('x_Birth'))

geographies = {

    "Garki_Single" : { "Geography": "Garki_Single",
                       "Air_Temperature_Filename":   "Garki_single_temperature.bin",
                       "Demographics_Filename":      "Garki_single_demographics.compiled.json", 
                       "Land_Temperature_Filename":  "Garki_single_temperature.bin",
                       "Rainfall_Filename":          "Garki_single_rainfall.bin", 
                       "Relative_Humidity_Filename": "Garki_single_humidity.bin",
                       "Enable_Climate_Stochasticity": 1, # every two weeks in raw data series
                       "Enable_Demographics_Other": 0 # no 'AbovePoverty' etc. in these files
                     },

    "Namawala" :     { "Geography": "Namawala",
                       "Air_Temperature_Filename":   "Namawala_single_node_air_temperature_daily.bin",
                       "Demographics_Filename":      "Namawala_single_node_demographics.compiled.json", 
                       "Land_Temperature_Filename":  "Namawala_single_node_land_temperature_daily.bin",
                       "Rainfall_Filename":          "Namawala_single_node_rainfall_daily.bin", 
                       "Relative_Humidity_Filename": "Namawala_single_node_relative_humidity_daily.bin",
                       "Enable_Climate_Stochasticity": 1, # every month in raw data series
                       "Enable_Demographics_Other": 0 # no 'AbovePoverty' etc. in these files
                     },

    "Sinamalima": {"Geography": "Zambia/Sinamalima_1_node",
                   "Demographics_Filename": "sinamalima_30arcsec_demographics_alt_600.json",
                   "Air_Temperature_Filename": "Zambia_30arcsec_air_temperature_daily.bin",
                   "Land_Temperature_Filename": "Zambia_30arcsec_air_temperature_daily.bin",
                   "Rainfall_Filename": "Zambia_30arcsec_rainfall_daily.bin", 
                   "Relative_Humidity_Filename": "Zambia_30arcsec_relative_humidity_daily.bin",
                   "Enable_Climate_Stochasticity": 0 # daily in raw data series
        },

    "Munyumbwe": {"Geography": "Zambia/Munyumbwe_1_node",
                  "Demographics_Filename": "munyumbwe_30arcsec_demographics_alt_800.json",
                  "Air_Temperature_Filename": "Zambia_30arcsec_air_temperature_daily.bin",
                  "Land_Temperature_Filename": "Zambia_30arcsec_air_temperature_daily.bin",
                  "Rainfall_Filename": "Zambia_30arcsec_rainfall_daily.bin", 
                  "Relative_Humidity_Filename": "Zambia_30arcsec_relative_humidity_daily.bin",
                  "Enable_Climate_Stochasticity": 0 # daily in raw data series
        },

    "Lukonde": {"Geography": "Zambia/Lukonde_1_node",
                "Demographics_Filename": "lukonde_30arcsec_demographics_alt_1000.json",
                "Air_Temperature_Filename": "Zambia_30arcsec_air_temperature_daily.bin",
                "Land_Temperature_Filename": "Zambia_30arcsec_air_temperature_daily.bin",
                "Rainfall_Filename": "Zambia_30arcsec_rainfall_daily.bin", 
                "Relative_Humidity_Filename": "Zambia_30arcsec_relative_humidity_daily.bin",
                "Enable_Climate_Stochasticity": 0 # daily in raw data series
        },

    "Gwembe": {"Geography": "Zambia/Gwembe_1_node",
               "Demographics_Filename": "gwembe_30arcsec_demographics_alt_1300.json",
               "Air_Temperature_Filename": "Zambia_30arcsec_air_temperature_daily.bin",
               "Land_Temperature_Filename": "Zambia_30arcsec_air_temperature_daily.bin",
               "Rainfall_Filename": "Zambia_30arcsec_rainfall_daily.bin", 
               "Relative_Humidity_Filename": "Zambia_30arcsec_relative_humidity_daily.bin",
               "Enable_Climate_Stochasticity": 0 # daily in raw data series
        },

    "Sinazongwe" :   { "Geography": "Zambia/Sinamalima_single_node",
                       "Air_Temperature_Filename":   "Zambia_Sinamalima_2_5arcmin_air_temperature_daily.bin",
                       "Demographics_Filename":      "Zambia_Sinamalima_single_node_demographics.compiled.json", 
                       "Land_Temperature_Filename":  "Zambia_Sinamalima_2_5arcmin_land_temperature_daily.bin",
                       "Rainfall_Filename":          "Zambia_Sinamalima_2_5arcmin_rainfall_daily.bin", 
                       "Relative_Humidity_Filename": "Zambia_Sinamalima_2_5arcmin_relative_humidity_daily.bin",
                       "Enable_Climate_Stochasticity": 0 # daily in raw data series
                     },

    "GwembeSinazongwePopCluster" : {
                       "Geography": "Zambia/Gwembe_Sinazongwe_pop_cluster",
                       #"Node_Grid_Size": 0.00833,    ## 30arcsec/3600
                       "Air_Temperature_Filename":   "Zambia_Gwembe_Sinazongwe_30arcsec_air_temperature_daily.bin",
                       "Demographics_Filename":      "Zambia_Gwembe_Sinazongwe_pop_cluster_demographics.compiled.json", 
                       "Land_Temperature_Filename":  "Zambia_Gwembe_Sinazongwe_30arcsec_land_temperature_daily.bin",
                       "Rainfall_Filename":          "Zambia_Gwembe_Sinazongwe_30arcsec_rainfall_daily.bin", 
                       "Relative_Humidity_Filename": "Zambia_Gwembe_Sinazongwe_30arcsec_relative_humidity_daily.bin",
                       "Enable_Climate_Stochasticity": 0, # daily in raw data series
                       "Enable_Local_Migration": 1, 
                       "Local_Migration_Filename":   "Zambia_Gwembe_Sinazongwe_pop_cluster_local_migration.bin"
                     },

    "Dielmo" :       { "Geography": "Senegal_Gambia/Dielmo_Ndiop",
                       "Air_Temperature_Filename":   "Senegal_Dielmo_Ndiop_2_5arcmin_air_temperature_daily.bin",
                       "Demographics_Filename":      "Senegal_Dielmo_single_node_demographics.static.compiled.json", 
                       "Land_Temperature_Filename":  "Senegal_Dielmo_Ndiop_2_5arcmin_land_temperature_daily.bin",
                       "Rainfall_Filename":          "Senegal_Dielmo_Ndiop_2_5arcmin_rainfall_daily.bin", 
                       "Relative_Humidity_Filename": "Senegal_Dielmo_Ndiop_2_5arcmin_relative_humidity_daily.bin",
                       "Enable_Climate_Stochasticity": 0 # daily in raw data series
                      },

    "Ndiop" :        { "Geography": "Senegal_Gambia/Dielmo_Ndiop",
                       "Air_Temperature_Filename":   "Senegal_Dielmo_Ndiop_2_5arcmin_air_temperature_daily.bin",
                       "Demographics_Filename":      "Senegal_Ndiop_single_node_demographics.static.compiled.json", 
                       "Land_Temperature_Filename":  "Senegal_Dielmo_Ndiop_2_5arcmin_land_temperature_daily.bin",
                       "Rainfall_Filename":          "Senegal_Dielmo_Ndiop_2_5arcmin_rainfall_daily.bin", 
                       "Relative_Humidity_Filename": "Senegal_Dielmo_Ndiop_2_5arcmin_relative_humidity_daily.bin",
                       "Enable_Climate_Stochasticity": 0 # daily in raw data series
                      },

    "Thies" :        { "Geography": "Senegal_Gambia/Thies",
                       "Air_Temperature_Filename":   "Senegal_Thies_2_5arcmin_air_temperature_daily.bin",
                       "Demographics_Filename":      "Senegal_Thies_single_node_demographics.static.compiled.json", 
                       "Land_Temperature_Filename":  "Senegal_Thies_2_5arcmin_land_temperature_daily.bin",
                       "Rainfall_Filename":          "Senegal_Thies_2_5arcmin_rainfall_daily.bin", 
                       "Relative_Humidity_Filename": "Senegal_Thies_2_5arcmin_relative_humidity_daily.bin",
                       "Enable_Climate_Stochasticity": 0 # daily in raw data series
                      },

    "Mocuba" :       { "Geography": "Mozambique_Zambezia",
                       "Air_Temperature_Filename":   "Mozambique_Zambezia_2_5arcmin_air_temperature_daily.bin",
                       "Demographics_Filename":      "Mozambique_Zambezia_Mocuba_single_node_demographics.compiled.json", 
                       "Land_Temperature_Filename":  "Mozambique_Zambezia_2_5arcmin_land_temperature_daily.bin",
                       "Rainfall_Filename":          "Mozambique_Zambezia_2_5arcmin_rainfall_daily.bin", 
                       "Relative_Humidity_Filename": "Mozambique_Zambezia_2_5arcmin_relative_humidity_daily.bin",
                       "Enable_Climate_Stochasticity": 0 # daily in raw data series
                      },

    "West_Kenya" :    { "Geography": "Kenya_Nyanza",
                        "Node_Grid_Size": 0.009,  ##
                        "Air_Temperature_Filename":   "Kenya_Nyanza_30arcsec_air_temperature_daily.bin",
                        "Demographics_Filename":      "Kenya_Nyanza_2node_demographics.compiled.json", 
                        "Enable_Local_Migration": 1, 
                        "Local_Migration_Filename":   "Kenya_Nyanza_2node_local_migration.bin",
                        "Land_Temperature_Filename":  "Kenya_Nyanza_30arcsec_land_temperature_daily.bin",
                        "Rainfall_Filename":          "Kenya_Nyanza_30arcsec_rainfall_daily.bin", 
                        "Relative_Humidity_Filename": "Kenya_Nyanza_30arcsec_relative_humidity_daily.bin",
                        "Enable_Climate_Stochasticity": 0 # daily in raw data series
                      },

    "Solomon_Islands" :   { "Geography": "Solomon_Islands/Honiara",
                            "Node_Grid_Size": 0.009,  ##
                            "Air_Temperature_Filename":   "Honiara_temperature_daily10y.bin",
                            "Demographics_Filename":      "Honiara_single_node_demographics.compiled.json", 
                            "Land_Temperature_Filename":  "Honiara_temperature_daily10y.bin",
                            "Rainfall_Filename":          "Honiara_rainfall_daily10y.bin", 
                            "Relative_Humidity_Filename": "Honiara_humidity_daily10y.bin",
                            "Enable_Climate_Stochasticity": 0 # daily in raw data series
                      },

    "Solomon_Islands_2Node" :   { "Geography": "Solomon_Islands/Honiara _Haleta",
                            "Node_Grid_Size": 0.009,  ##
                            "Air_Temperature_Filename":   "Honiara_Haleta_temperature_daily10y.bin",
                            "Demographics_Filename":      "Honiara_Haleta_two_node_demographics.compiled.json", 
                            "Enable_Local_Migration": 1, 
                            "Local_Migration_Filename":   "Honiara_Haleta_two_node_local_migration.bin",
                            "Land_Temperature_Filename":  "Honiara_Haleta_temperature_daily10y.bin",
                            "Rainfall_Filename":          "Honiara_Haleta_rainfall_daily10y.bin", 
                            "Relative_Humidity_Filename": "Honiara_Haleta_humidity_daily10y.bin",
                            "Enable_Climate_Stochasticity": 0 # daily in raw data series
                      },

    "Nabang" :    { "Geography": "UCIrvine/Nabang",
                        "Node_Grid_Size": 0.009,  ##
                        "Air_Temperature_Filename":   "China_Nabang_2_5arcmin_air_temperature_daily.bin",
                        "Demographics_Filename":      "Nabang_two_node_demographics.compiled.json", 
                        "Enable_Local_Migration": 1, 
                        "Local_Migration_Filename":   "Nabang_two_node_local_migration.bin",
                        "Land_Temperature_Filename":  "China_Nabang_2_5arcmin_air_temperature_daily.bin",
                        "Rainfall_Filename":          "China_Nabang_2_5arcmin_rainfall_daily.bin", 
                        "Relative_Humidity_Filename": "China_Nabang_2_5arcmin_relative_humidity_daily.bin",
                        "Enable_Climate_Stochasticity": 0 # daily in raw data series
                      },

     "Tha_Song_Yang" :    { "Geography": "Tha_Song_Yang",
                        "Node_Grid_Size": 0.009,  ##
                        "Air_Temperature_Filename":   "Thailand_Tha_Song_Yang_2_5arcmin_air_temperature_daily.bin",
                        "Demographics_Filename":      "TSY_two_node_demographics.compiled.json", 
                        "Enable_Local_Migration": 1, 
                        "Local_Migration_Filename":   "TSY_two_node_local_migration.bin",
                        "Land_Temperature_Filename":  "Thailand_Tha_Song_Yang_2_5arcmin_air_temperature_daily.bin",
                        "Rainfall_Filename":          "Thailand_Tha_Song_Yang_2_5arcmin_rainfall_daily.bin", 
                        "Relative_Humidity_Filename": "Thailand_Tha_Song_Yang_2_5arcmin_relative_humidity_daily.bin",
                        "Enable_Climate_Stochasticity": 0 # daily in raw data series
                      },

    "Malariatherapy" : {  "Geography": "Calibration",
                          "Demographics_Filename": "Malariatherapy_demographics.compiled.json",
                          "Base_Population_Scale_Factor" : 2,
                          "Enable_Vital_Dynamics" : 0,
                          "Climate_Model" : "CLIMATE_CONSTANT" # no mosquitoes in challenge trial setting
                      },

    "Birth_Cohort" : { "Geography": "Calibration",
                       "Demographics_Filename": "birth_cohort_demographics.compiled.json", 
                       'Base_Population_Scale_Factor' : 10,
                       'Enable_Vital_Dynamics' : 0, # No births/deaths.  Just following a birth cohort.
                       "Climate_Model" : "CLIMATE_CONSTANT" # no mosquitoes
                     }
}