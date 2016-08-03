import logging
import os

from dtk.generic.demographics import set_static_demographics
from dtk.utils.ioformat.OutputMessage import OutputMessage


def convert_filepaths(params):
    """
    Make sure to add the geography folder in front of the paths.
    For example, if the geography is Namawala, we want the climate/demographics files to be Namawala\\file.json

    :param params: The config parameters
    :return: Nothing

    """
    g = params.pop('Geography', None)
    if not g: return
    for k, v in params.items():
        if k == 'Demographics_Filenames':
            params[k] = [os.path.join(g, fn) for fn in v]
        elif k == 'Campaign_Filename':
            continue
        elif 'Filename' in k:
            params[k] = os.path.join(g, v)


def get_converted_paths_for_geography(geography):
    """
    Returns the converted paths for a given geography.

    Simply copy the geography specific parameters and send it to the :any:'convert_filepaths' function to get the correct paths.
    Then return the updated parameters.

    :param geography: The selected geography
    :return: parameters with the correct path

    """
    params = geographies.get(geography).copy()
    if not params:
        raise Exception('%s geography not yet implemented' % geography)

    convert_filepaths(params)

    return params


def get_geography_parameter(geography, param):
    """
    Return a particular parameter for a given geography.
    This function will return the parameter value with the updated path and can accommodate geography of the form:
    ``Sinazongwe.static``. The ``.static`` will be removed.

    :param geography: The desired geography
    :param param: The parameter we want to retrieve
    :return: The value of the parameter for the given geography
    """
    geography = geography.split('.')[0]  # e.g. Sinazongwe.static
    params = get_converted_paths_for_geography(geography)
    return params.get(param)


def set_geography(cb, geography, static=False, pop_scale=1):
    """
    Set the demographics in a given :py:class:`DTKConfigBuilder` for the selected geography.
    The demographics can be set to static and created with the :any:`set_static_demographics` function or it can be created
    with the population scale parameter passed.

    .. note:: The population scale will act on the ``x_Birth`` configuration parameter if the ``Birth_Rate_dependence`` is set to a ``FIXED_BIRTH_DATE``. It will also act on the ``Base_Population_Scale_Factor``.

    :param cb: The :py:class:`DTKConfigBuilder` containing the current configuration
    :param geography: The selected geography
    :param static: If True, will create a static demographics. if False, will use the ``pop_scale``
    :param pop_scale: Used if the demographics is not static and will
    :return: Nothing
    """
    params = get_converted_paths_for_geography(geography)
    logging.debug('Geography parameters: %s' % params)
    cb.update_params(params)
    if static:
        set_static_demographics(cb, use_existing=True)
    if pop_scale != 1:
        cb.set_param('Base_Population_Scale_Factor', pop_scale * cb.get_param('Base_Population_Scale_Factor'))
        if cb.get_param('Birth_Rate_Dependence') == 'FIXED_BIRTH_RATE':
            cb.set_param('x_Birth', pop_scale * cb.get_param('x_Birth'))


geographies = {

    "Garki_Single": {"Geography": "Garki_Single",
                     "Air_Temperature_Filename": "Garki_single_temperature.bin",
                     "Demographics_Filenames": ["Garki_single_demographics.compiled.json"],
                     "Land_Temperature_Filename": "Garki_single_temperature.bin",
                     "Rainfall_Filename": "Garki_single_rainfall.bin",
                     "Relative_Humidity_Filename": "Garki_single_humidity.bin",
                     "Enable_Climate_Stochasticity": 1,  # every two weeks in raw data series
                     "Enable_Demographics_Other": 0  # no 'AbovePoverty' etc. in these files
                     },

    "Namawala": {"Geography": "Namawala",
                 "Air_Temperature_Filename": "Namawala_single_node_air_temperature_daily.bin",
                 "Demographics_Filenames": ["Namawala_single_node_demographics.compiled.json"],
                 "Land_Temperature_Filename": "Namawala_single_node_land_temperature_daily.bin",
                 "Rainfall_Filename": "Namawala_single_node_rainfall_daily.bin",
                 "Relative_Humidity_Filename": "Namawala_single_node_relative_humidity_daily.bin",
                 "Enable_Climate_Stochasticity": 1,  # every month in raw data series
                 "Enable_Demographics_Other": 0  # no 'AbovePoverty' etc. in these files
                 },

    "Sinamalima": {"Geography": "Zambia/Sinamalima_1_node",
                   "Demographics_Filenames": ["sinamalima_30arcsec_demographics_alt_600.json"],
                   "Air_Temperature_Filename": "Zambia_30arcsec_air_temperature_daily.bin",
                   "Land_Temperature_Filename": "Zambia_30arcsec_air_temperature_daily.bin",
                   "Rainfall_Filename": "Zambia_30arcsec_rainfall_daily.bin",
                   "Relative_Humidity_Filename": "Zambia_30arcsec_relative_humidity_daily.bin",
                   "Enable_Climate_Stochasticity": 0  # daily in raw data series
                   },

    "Munyumbwe": {"Geography": "Zambia/Munyumbwe_1_node",
                  "Demographics_Filenames": ["munyumbwe_30arcsec_demographics_alt_800.json"],
                  "Air_Temperature_Filename": "Zambia_30arcsec_air_temperature_daily.bin",
                  "Land_Temperature_Filename": "Zambia_30arcsec_air_temperature_daily.bin",
                  "Rainfall_Filename": "Zambia_30arcsec_rainfall_daily.bin",
                  "Relative_Humidity_Filename": "Zambia_30arcsec_relative_humidity_daily.bin",
                  "Enable_Climate_Stochasticity": 0  # daily in raw data series
                  },

    "Lukonde": {"Geography": "Zambia/Lukonde_1_node",
                "Demographics_Filenames": ["lukonde_30arcsec_demographics_alt_1000.json"],
                "Air_Temperature_Filename": "Zambia_30arcsec_air_temperature_daily.bin",
                "Land_Temperature_Filename": "Zambia_30arcsec_air_temperature_daily.bin",
                "Rainfall_Filename": "Zambia_30arcsec_rainfall_daily.bin",
                "Relative_Humidity_Filename": "Zambia_30arcsec_relative_humidity_daily.bin",
                "Enable_Climate_Stochasticity": 0  # daily in raw data series
                },

    "Gwembe": {"Geography": "Zambia/Gwembe_1_node",
               "Demographics_Filenames": ["gwembe_30arcsec_demographics_alt_1300.json"],
               "Air_Temperature_Filename": "Zambia_30arcsec_air_temperature_daily.bin",
               "Land_Temperature_Filename": "Zambia_30arcsec_air_temperature_daily.bin",
               "Rainfall_Filename": "Zambia_30arcsec_rainfall_daily.bin",
               "Relative_Humidity_Filename": "Zambia_30arcsec_relative_humidity_daily.bin",
               "Enable_Climate_Stochasticity": 0  # daily in raw data series
               },

    "Sinazongwe": {"Geography": "Zambia/Sinamalima_single_node",
                   "Air_Temperature_Filename": "Zambia_Sinamalima_2_5arcmin_air_temperature_daily.bin",
                   "Demographics_Filenames": ["Zambia_Sinamalima_single_node_demographics.compiled.json"],
                   "Land_Temperature_Filename": "Zambia_Sinamalima_2_5arcmin_land_temperature_daily.bin",
                   "Rainfall_Filename": "Zambia_Sinamalima_2_5arcmin_rainfall_daily.bin",
                   "Relative_Humidity_Filename": "Zambia_Sinamalima_2_5arcmin_relative_humidity_daily.bin",
                   "Enable_Climate_Stochasticity": 0  # daily in raw data series
                   },

    "Sinamalima_1_node": {"Geography": "Zambia/Sinamalima_1_node",
                          "Air_Temperature_Filename": "Zambia_30arcsec_air_temperature_daily.bin",
                          "Demographics_Filenames": ["sinamalima_30arcsec_demographics_alt_600.json"],
                          "Land_Temperature_Filename": "Zambia_30arcsec_air_temperature_daily.bin",
                          "Rainfall_Filename": "Zambia_30arcsec_rainfall_daily.bin",
                          "Relative_Humidity_Filename": "Zambia_30arcsec_relative_humidity_daily.bin",
                          "Enable_Climate_Stochasticity": 0  # daily in raw data series
                          },

    "Gwembe_1_node": {"Geography": "Zambia/Gwembe_1_node",
                      "Air_Temperature_Filename": "Zambia_30arcsec_air_temperature_daily.bin",
                      "Demographics_Filenames": ["gwembe_30arcsec_demographics_alt_1300.json"],
                      "Land_Temperature_Filename": "Zambia_30arcsec_air_temperature_daily.bin",
                      "Rainfall_Filename": "Zambia_30arcsec_rainfall_daily.bin",
                      "Relative_Humidity_Filename": "Zambia_30arcsec_relative_humidity_daily.bin",
                      "Enable_Climate_Stochasticity": 0  # daily in raw data series
                      },

    "Lukonde_1_node": {"Geography": "Zambia/Lukonde_1_node",
                       "Air_Temperature_Filename": "Zambia_30arcsec_air_temperature_daily.bin",
                       "Demographics_Filenames": ["lukonde_30arcsec_demographics_alt_1000.json"],
                       "Land_Temperature_Filename": "Zambia_30arcsec_air_temperature_daily.bin",
                       "Rainfall_Filename": "Zambia_30arcsec_rainfall_daily.bin",
                       "Relative_Humidity_Filename": "Zambia_30arcsec_relative_humidity_daily.bin",
                       "Enable_Climate_Stochasticity": 0  # daily in raw data series
                       },

    "Munumbwe_1_node": {"Geography": "Zambia/Munumbwe_1_node",
                        "Air_Temperature_Filename": "Zambia_30arcsec_air_temperature_daily.bin",
                        "Demographics_Filenames": ["munumbwe_30arcsec_demographics_alt_800.json"],
                        "Land_Temperature_Filename": "Zambia_30arcsec_air_temperature_daily.bin",
                        "Rainfall_Filename": "Zambia_30arcsec_rainfall_daily.bin",
                        "Relative_Humidity_Filename": "Zambia_30arcsec_relative_humidity_daily.bin",
                        "Enable_Climate_Stochasticity": 0  # daily in raw data series
                        },

    "Gwembe_Sinazongwe_115_nodes": {
        "Geography": "Zambia/Gwembe_Sinazongwe_115_nodes",
        "Air_Temperature_Filename": "Zambia_30arcsec_air_temperature_daily.bin",
        "Land_Temperature_Filename": "Zambia_30arcsec_air_temperature_daily.bin",
        "Rainfall_Filename": "Zambia_30arcsec_rainfall_daily.bin",
        "Relative_Humidity_Filename": "Zambia_30arcsec_relative_humidity_daily.bin",
        "Enable_Climate_Stochasticity": 0,  # daily in raw data series
        # "Enable_Local_Migration": 0,
        # "x_Local_Migration": 0 ,
        # "Local_Migration_Filename":   "Zambia_Gwembe_Sinazongwe_115_nodes_local_migration.bin",
        # "Node_Grid_Size": 0.00833,    ## 30arcsec/3600
        # "Demographics_Filenames": ["Zambia_30arcsec_demographics.json"],
    },

    "GwembeSinazongwePopCluster": {
        "Geography": "Zambia/GwembeSinazongwePopCluster",
        "Air_Temperature_Filename": "Zambia_30arcsec_air_temperature_daily.bin",
        "Land_Temperature_Filename": "Zambia_30arcsec_air_temperature_daily.bin",
        "Rainfall_Filename": "Zambia_30arcsec_rainfall_daily.bin",
        "Relative_Humidity_Filename": "Zambia_30arcsec_relative_humidity_daily.bin",
        "Enable_Climate_Stochasticity": 0,  # daily in raw data series
        "Enable_Local_Migration": 1,
        "Local_Migration_Filename": "Zambia_Gwembe_Sinazongwe_121_nodes_local_migration.bin"
        # "Node_Grid_Size": 0.00833,    ## 30arcsec/3600
        # "Demographics_Filenames":      ["Zambia_30arcsec_demographics.json"],
    },

    "Dielmo": {"Geography": "Senegal_Gambia/Dielmo_Ndiop",
               "Air_Temperature_Filename": "Senegal_Dielmo_Ndiop_2_5arcmin_air_temperature_daily.bin",
               "Demographics_Filenames": ["Senegal_Dielmo_single_node_demographics.static.compiled.json"],
               "Land_Temperature_Filename": "Senegal_Dielmo_Ndiop_2_5arcmin_land_temperature_daily.bin",
               "Rainfall_Filename": "Senegal_Dielmo_Ndiop_2_5arcmin_rainfall_daily.bin",
               "Relative_Humidity_Filename": "Senegal_Dielmo_Ndiop_2_5arcmin_relative_humidity_daily.bin",
               "Enable_Climate_Stochasticity": 0  # daily in raw data series
               },

    "Ndiop": {"Geography": "Senegal_Gambia/Dielmo_Ndiop",
              "Air_Temperature_Filename": "Senegal_Dielmo_Ndiop_2_5arcmin_air_temperature_daily.bin",
              "Demographics_Filenames": ["Senegal_Ndiop_single_node_demographics.static.compiled.json"],
              "Land_Temperature_Filename": "Senegal_Dielmo_Ndiop_2_5arcmin_land_temperature_daily.bin",
              "Rainfall_Filename": "Senegal_Dielmo_Ndiop_2_5arcmin_rainfall_daily.bin",
              "Relative_Humidity_Filename": "Senegal_Dielmo_Ndiop_2_5arcmin_relative_humidity_daily.bin",
              "Enable_Climate_Stochasticity": 0  # daily in raw data series
              },

    "Thies": {"Geography": "Senegal_Gambia/Thies",
              "Air_Temperature_Filename": "Senegal_Thies_2_5arcmin_air_temperature_daily.bin",
              "Demographics_Filenames": ["Senegal_Thies_single_node_demographics.static.compiled.json"],
              "Land_Temperature_Filename": "Senegal_Thies_2_5arcmin_land_temperature_daily.bin",
              "Rainfall_Filename": "Senegal_Thies_2_5arcmin_rainfall_daily.bin",
              "Relative_Humidity_Filename": "Senegal_Thies_2_5arcmin_relative_humidity_daily.bin",
              "Enable_Climate_Stochasticity": 0  # daily in raw data series
              },

    "Mocuba": {"Geography": "Mozambique_Zambezia",
               "Air_Temperature_Filename": "Mozambique_Zambezia_2_5arcmin_air_temperature_daily.bin",
               "Demographics_Filenames": ["Mozambique_Zambezia_Mocuba_single_node_demographics.compiled.json"],
               "Land_Temperature_Filename": "Mozambique_Zambezia_2_5arcmin_land_temperature_daily.bin",
               "Rainfall_Filename": "Mozambique_Zambezia_2_5arcmin_rainfall_daily.bin",
               "Relative_Humidity_Filename": "Mozambique_Zambezia_2_5arcmin_relative_humidity_daily.bin",
               "Enable_Climate_Stochasticity": 0  # daily in raw data series
               },

    "West_Kenya": {"Geography": "Kenya_Nyanza",
                   "Node_Grid_Size": 0.009,  ##
                   "Air_Temperature_Filename": "Kenya_Nyanza_30arcsec_air_temperature_daily.bin",
                   "Demographics_Filenames": ["Kenya_Nyanza_2node_demographics.compiled.json"],
                   "Enable_Local_Migration": 1,
                   "Local_Migration_Filename": "Kenya_Nyanza_2node_local_migration.bin",
                   "Land_Temperature_Filename": "Kenya_Nyanza_30arcsec_land_temperature_daily.bin",
                   "Rainfall_Filename": "Kenya_Nyanza_30arcsec_rainfall_daily.bin",
                   "Relative_Humidity_Filename": "Kenya_Nyanza_30arcsec_relative_humidity_daily.bin",
                   "Enable_Climate_Stochasticity": 0  # daily in raw data series
                   },

    "Solomon_Islands": {"Geography": "Solomon_Islands/Honiara",
                        "Node_Grid_Size": 0.009,  ##
                        "Air_Temperature_Filename": "Honiara_temperature_daily10y.bin",
                        "Demographics_Filenames": ["Honiara_single_node_demographics.compiled.json"],
                        "Land_Temperature_Filename": "Honiara_temperature_daily10y.bin",
                        "Rainfall_Filename": "Honiara_rainfall_daily10y.bin",
                        "Relative_Humidity_Filename": "Honiara_humidity_daily10y.bin",
                        "Enable_Climate_Stochasticity": 0  # daily in raw data series
                        },

    "Solomon_Islands_2Node": {"Geography": "Solomon_Islands/Honiara _Haleta",
                              "Node_Grid_Size": 0.009,  ##
                              "Air_Temperature_Filename": "Honiara_Haleta_temperature_daily10y.bin",
                              "Demographics_Filenames": ["Honiara_Haleta_two_node_demographics.compiled.json"],
                              "Enable_Local_Migration": 1,
                              "Local_Migration_Filename": "Honiara_Haleta_two_node_local_migration.bin",
                              "Land_Temperature_Filename": "Honiara_Haleta_temperature_daily10y.bin",
                              "Rainfall_Filename": "Honiara_Haleta_rainfall_daily10y.bin",
                              "Relative_Humidity_Filename": "Honiara_Haleta_humidity_daily10y.bin",
                              "Enable_Climate_Stochasticity": 0  # daily in raw data series
                              },

    "Nabang": {"Geography": "UCIrvine/Nabang",
               "Node_Grid_Size": 0.009,  ##
               "Air_Temperature_Filename": "China_Nabang_2_5arcmin_air_temperature_daily.bin",
               "Demographics_Filenames": ["Nabang_two_node_demographics.compiled.json"],
               "Enable_Local_Migration": 1,
               "Local_Migration_Filename": "Nabang_two_node_local_migration.bin",
               "Land_Temperature_Filename": "China_Nabang_2_5arcmin_air_temperature_daily.bin",
               "Rainfall_Filename": "China_Nabang_2_5arcmin_rainfall_daily.bin",
               "Relative_Humidity_Filename": "China_Nabang_2_5arcmin_relative_humidity_daily.bin",
               "Enable_Climate_Stochasticity": 0  # daily in raw data series
               },

    "Tha_Song_Yang": {"Geography": "Tha_Song_Yang",
                      "Node_Grid_Size": 0.009,  ##
                      "Air_Temperature_Filename": "Thailand_Tha_Song_Yang_2_5arcmin_air_temperature_daily.bin",
                      "Demographics_Filenames": ["TSY_two_node_demographics.compiled.json"],
                      "Enable_Local_Migration": 1,
                      "Local_Migration_Filename": "TSY_two_node_local_migration.bin",
                      "Land_Temperature_Filename": "Thailand_Tha_Song_Yang_2_5arcmin_air_temperature_daily.bin",
                      "Rainfall_Filename": "Thailand_Tha_Song_Yang_2_5arcmin_rainfall_daily.bin",
                      "Relative_Humidity_Filename": "Thailand_Tha_Song_Yang_2_5arcmin_relative_humidity_daily.bin",
                      "Enable_Climate_Stochasticity": 0  # daily in raw data series
                      },

    "Malariatherapy": {"Geography": "Calibration",
                       "Demographics_Filenames": ["Malariatherapy_demographics.compiled.json"],
                       "Base_Population_Scale_Factor": 2,
                       "Enable_Vital_Dynamics": 0,
                       "Climate_Model": "CLIMATE_CONSTANT"  # no mosquitoes in challenge trial setting
                       },

    "Birth_Cohort": {"Geography": "Calibration",
                     "Demographics_Filenames": ["birth_cohort_demographics.compiled.json"],
                     'Base_Population_Scale_Factor': 10,
                     'Enable_Vital_Dynamics': 0,  # No births/deaths.  Just following a birth cohort.
                     "Climate_Model": "CLIMATE_CONSTANT"  # no mosquitoes
                     },

    "Household": {"Geography": "Household",
                  "Listed_Events": ["VaccinateNeighbors", "Blackout", "Distributing_AntimalariaDrug", 'TestedPositive',
                                    'Give_Drugs', 'Spray_IRS', 'Drug_Campaign_Blackout', 'IRS_Blackout', 'Node_Sprayed',
                                    'Received_Campaign_Drugs', 'Received_Treatment', 'Received_ITN', 'Received_Vehicle',
                                    'Received_Test', 'Received_RCD_Drugs', 'Received_Survey'] + ["Diagnostic_Survey_%d" % x for x in
                                                                              range(5)],
                  "Report_Event_Recorder_Events": ["NewClinicalCase", 'Received_Campaign_Drugs', 'Received_RCD_Drugs',
                                                   'Received_Treatment', 'TestedPositive', 'Received_ITN',
                                                   'Received_Test', 'Node_Sprayed', 'Received_Survey'],

                  "Enable_Climate_Stochasticity": 0,  # daily in raw data series
                  "Climate_Model": "CLIMATE_BY_DATA",
                  'Enable_Nondisease_Mortality': 1,
                  "Minimum_Adult_Age_Years": 15,
                  "Birth_Rate_Dependence": "FIXED_BIRTH_RATE",
                  "Enable_Demographics_Other": 0,
                  "Enable_Demographics_Initial": 1,
                  "Enable_Vital_Dynamics": 1,

                  "Enable_Migration_Heterogeneity": 1,
                  "Migration_Model": "FIXED_RATE_MIGRATION",
                  "Enable_Local_Migration": 1,
                  "Enable_Regional_Migration": 0,
                  "Migration_Pattern": "SINGLE_ROUND_TRIPS",
                  "Local_Migration_Roundtrip_Duration": 3.0,
                  "Local_Migration_Roundtrip_Probability": 1.0,
                  "x_Local_Migration": 0.1,
                  "Enable_Sea_Demographics_Modifiers": 0,
                  "Enable_Sea_Family_Migration": 0,

                  "Vector_Sampling_Type": "TRACK_ALL_VECTORS",
                  "Enable_Vector_Aging": 1,
                  "Enable_Vector_Mortality": 1,
                  "Enable_Vector_Migration": 1,
                  "Enable_Vector_Migration_Local": 1,
                  "Enable_Vector_Migration_Regional": 1,
                  "Vector_Migration_Modifier_Equation": "EXPONENTIAL",
                  "x_Vector_Migration_Local": 100,
                  "x_Vector_Migration_Regional": 0.1,
                  "Vector_Migration_Habitat_Modifier": 3.8,
                  "Vector_Migration_Food_Modifier": 0,
                  "Vector_Migration_Stay_Put_Modifier": 10
                  }
}
