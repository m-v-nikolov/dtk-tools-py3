import numpy as np
import sys

def add_ITN_age_season(config_builder, start=1, coverage_all=1, waning={}, discard={},
                       age_dep={}, seasonal_dep={}, cost=5, nodeIDs=[], as_birth=False, duration=-1,
                       trigger_string_list=[]):

    """
    Add an ITN intervention to the config_builder passed.
    You will need to add the following custom events:
        "Bednet_Discarded",
        "Bednet_Got_New_One",
        "Bednet_Using"
    :param config_builder: The :py:class:`DTKConfigBuilder <dtk.utils.core.DTKConfigBuilder>` holding the campaign that will receive the ITN event
    :param start: The start day of the bed net distribution
    :param coverage_all: Fraction of the population receiving bed nets in a given distribution event
    :param waning: A dictionary defining the durability and initial potency of killing and blocking. Rates assume exponential decay.
    :param discard: A dictionary defining the net retention rates. Default is no discarding of nets.
    :param age_dep: A dictionary defining the age dependence of net use. Default is uniform across all ages.
    :param seasonal_dep: A dictionary defining the seasonal dependence of net use. Default is constant use during the year.
    :param cost: Set the ``Cost_To_Consumer`` parameter
    :param nodeIDs: If empty, all nodes will get the intervention. If set, only the nodeIDs specified will receive the intervention.
    :param as_birth: If true, event is specified as a birth-triggered intervention.
    :param duration: If run as a birth-triggered event, specifies the duration for the distribution to continue. Default
    is to continue until the end of the simulation.
    :param trigger_string_list: sets up a NodeLevelHealthTriggeredIV that listens for the defined trigger string event before giving out the intervention,
    "as_birth" and "trigger_string_list" options are mutually exclusive, if "as_birth" is true, trigger_string_list will be ignored.
    :return: Nothing
    """

    # Assign net protective properties #
    # Unless specified otherwise, use the default values
    kill_initial = 0.6
    block_initial = 0.9
    kill_decay = 1460
    block_decay = 730

    if waning:
        if 'kill_initial' in waning.keys():
            kill_initial = waning['kill_initial']

        if 'block_initial' in waning.keys():
            block_initial = waning['block_initial']

        if 'kill_decay' in waning.keys():
            kill_decay = waning['kill_decay']

        if 'block_decay' in waning.keys():
            block_decay = waning['block_decay']

    # Assign seasonal net usage #
    # Times are days of the year
    # Input can be provided either as (times, values) for linear spline or (min coverage, day of maximum coverage)
    # under the assumption of sinusoidal dynamics. In the first case, the same value should be provided
    # for both 0 and 365; times > 365 will be ignored.
    if all([k in seasonal_dep.keys() for k in ['times','values']]):
        seasonal_times = seasonal_dep['times']
        seasonal_values = seasonal_dep['values']
    elif all([k in seasonal_dep.keys() for k in ['min_cov','max_day']]):
        seasonal_times = np.append(np.arange(0,361,30),365)
        if seasonal_dep['min_cov']==0:
            seasonal_dep['min_cov'] = seasonal_dep['min_cov'] + sys.float_info.epsilon
        seasonal_values = (1-seasonal_dep['min_cov'])/2*np.cos(2*np.pi/365*(seasonal_times-seasonal_dep['max_day']))+\
                      (1+seasonal_dep['min_cov'])/2
    else:
        seasonal_times = np.append(np.arange(0, 361, 30), 365)
        seasonal_values = np.linspace(1, 1, len(seasonal_times))

    # Assign age-dependent net usage #
    # Times are ages in years (note difference from seasonal dependence)
    if all([k in age_dep.keys() for k in ['times','values']]):
        age_times = age_dep['times']
        age_values = age_dep['values']
    elif all([k in age_dep.keys() for k in ['youth_cov','youth_min_age','youth_max_age']]):
        age_times = [0, age_dep['youth_min_age']-0.1, age_dep['youth_min_age'],
                     age_dep['youth_max_age']-0.1, age_dep['youth_max_age']]
        age_values = [1, 1, age_dep['youth_cov'], age_dep['youth_cov'], 1]
    else:
        age_times = [0, 125] # Dan B has hard-coded an upper limit of 125, will return error for larger values
        age_values = [1, 1]

    # Assign net ownership retention times #
    # Mean discard times in days; coverage half-life is discard time * ln(2)
    if all([k in discard.keys() for k in ['halflife1','halflife2','fraction1']]): # Two retention subgroups
        discard_time1 = discard['halflife1']
        discard_time2 = discard['halflife2']
        discard_fraction1 = discard['fraction1']
    elif 'halflife' in discard.keys():  # Single mean retention time
        discard_time1 = discard['halflife']
        discard_time2 = 365*40
        discard_fraction1 = 1
    else:                               # No discard of nets
        discard_time1 = 365*40
        discard_time2 = 365*40
        discard_fraction1 = 1

    # Assign node IDs #
    # Defaults to all nodes unless a node set is specified
    if not nodeIDs:
        nodeset_config = {"class": "NodeSetAll"}
    else:
        nodeset_config = {"class": "NodeSetNodeList", "Node_List": nodeIDs}

    # Generate ITN campaign event #
    # General or birth-triggered
    if as_birth:
        itn_event = {
            "Event_Coordinator_Config": {
                "Intervention_Config": {
                    "Actual_IndividualIntervention_Config": {
                        "Intervention_List": [
                            {
                                "Bednet_Type": "ITN",
                                "Blocking_Config": {
                                    "Decay_Time_Constant": block_decay,
                                    "Initial_Effect": block_initial,
                                    "class": "WaningEffectExponential"
                                },
                                "Cost_To_Consumer": cost,
                                "Killing_Config": {
                                    "Decay_Time_Constant": kill_decay,
                                    "Initial_Effect": kill_initial,
                                    "class": "WaningEffectExponential"
                                },
                                "Usage_Config_List":
                                    [
                                        {
                                            "class": "WaningEffectMapLinearAge",
                                            "Initial_Effect": 1.0,
                                            "Durability_Map":
                                                {
                                                    "Times": list(age_times),
                                                    "Values": list(age_values)
                                                }
                                        } ,
                                        {
                                            "class": "WaningEffectMapLinearSeasonal",
                                            "Initial_Effect": 1.0,
                                            "Durability_Map":
                                                {
                                                    "Times": list(seasonal_times),
                                                    "Values": list(seasonal_values)
                                                }
                                        }
                                    ],
                                "class": "UsageDependentBednet",
                                "Received_Event": "Bednet_Got_New_One",
                                "Using_Event": "Bednet_Using",
                                "Discard_Event": "Bednet_Discarded",
                                "Expiration_Distribution_Type": "DUAL_TIMESCALE_DURATION",
                                "Expiration_Period_1": discard_time1,
                                "Expiration_Period_2": discard_time2,
                                "Expiration_Percentage_Period_1": discard_fraction1

                            },
                        ],
                        "class": "MultiInterventionDistributor"
                    },
                    "Demographic_Coverage": coverage_all,
                    "Duration": duration,
                    "class": "BirthTriggeredIV"
                },
                "class": "StandardInterventionDistributionEventCoordinator"
            },
            "Nodeset_Config": nodeset_config,
            "Start_Day": start,
            "class": "CampaignEvent"
        }

    else:
        if trigger_string_list:
            itn_event = {
                "Event_Coordinator_Config": {
                    "Intervention_Config": {
                        "Blackout_On_First_Occurrence": 1,
                        "Demographic_Coverage": 1,
                        "Target_Residents_Only": 1,
                        "Trigger_Condition_List": trigger_string_list,
                        "class": "NodeLevelHealthTriggeredIV",
                        "Actual_IndividualIntervention_Config":{
                            "Intervention_List": [
                                {
                                    "Bednet_Type": "ITN",
                                    "Blocking_Config": {
                                        "Decay_Time_Constant": block_decay,
                                        "Initial_Effect": block_initial,
                                        "class": "WaningEffectExponential"
                                    },
                                    "Cost_To_Consumer": cost,
                                    "Killing_Config": {
                                        "Decay_Time_Constant": kill_decay,
                                        "Initial_Effect": kill_initial,
                                        "class": "WaningEffectExponential"
                                    },
                                    "Usage_Config_List":
                                        [
                                            {
                                                "class": "WaningEffectMapLinearAge",
                                                "Initial_Effect": 1.0,
                                                "Durability_Map":
                                                    {
                                                        "Times": list(age_times),
                                                        "Values": list(age_values)
                                                    }
                                            },
                                            {
                                                "class": "WaningEffectMapLinearSeasonal",
                                                "Initial_Effect": 1.0,
                                                "Durability_Map":
                                                    {
                                                        "Times": list(seasonal_times),
                                                        "Values": list(seasonal_values)
                                                    }
                                            }
                                        ],
                                    "class": "UsageDependentBednet",
                                    "Received_Event": "Bednet_Got_New_One",
                                    "Using_Event": "Bednet_Using",
                                    "Discard_Event": "Bednet_Discarded",
                                    "Expiration_Distribution_Type": "DUAL_TIMESCALE_DURATION",
                                    "Expiration_Period_1": discard_time1,
                                    "Expiration_Period_2": discard_time2,
                                    "Expiration_Percentage_Period_1": discard_fraction1
                                },
                            ],
                        "class": "MultiInterventionDistributor"
                        }
                    },
                    "class": "StandardInterventionDistributionEventCoordinator",
                    "Target_Demographic": "Everyone",
                    "Demographic_Coverage": coverage_all,
                    "Duration": duration
                },
                "Nodeset_Config": nodeset_config,
                "Start_Day": start,
                "class": "CampaignEvent"
            }
        else:
            itn_event = {
                "Event_Coordinator_Config": {
                    "Intervention_Config": {
                        "Intervention_List": [
                            {
                                "Bednet_Type": "ITN",
                                "Blocking_Config": {
                                    "Decay_Time_Constant": block_decay,
                                    "Initial_Effect": block_initial,
                                    "class": "WaningEffectExponential"
                                },
                                "Cost_To_Consumer": cost,
                                "Killing_Config": {
                                    "Decay_Time_Constant": kill_decay,
                                    "Initial_Effect": kill_initial,
                                    "class": "WaningEffectExponential"
                                },
                                "Usage_Config_List":
                                    [
                                        {
                                            "class": "WaningEffectMapLinearAge",
                                            "Initial_Effect": 1.0,
                                            "Durability_Map":
                                                {
                                                    "Times": list(age_times),
                                                    "Values": list(age_values)
                                                }
                                        },
                                        {
                                            "class": "WaningEffectMapLinearSeasonal",
                                            "Initial_Effect": 1.0,
                                            "Durability_Map":
                                                {
                                                    "Times": list(seasonal_times),
                                                    "Values": list(seasonal_values)
                                                }
                                        }
                                    ],
                                "class": "UsageDependentBednet",
                                "Received_Event": "Bednet_Got_New_One",
                                "Using_Event": "Bednet_Using",
                                "Discard_Event": "Bednet_Discarded",
                                "Expiration_Distribution_Type": "DUAL_TIMESCALE_DURATION",
                                "Expiration_Period_1": discard_time1,
                                "Expiration_Period_2": discard_time2,
                                "Expiration_Percentage_Period_1": discard_fraction1
                            },
                        ],
                        "class": "MultiInterventionDistributor"
                    },
                    "class": "StandardInterventionDistributionEventCoordinator",
                    "Target_Demographic": "Everyone",
                    "Demographic_Coverage": coverage_all,
                    "Duration": duration
                },
                "Nodeset_Config": nodeset_config,
                "Start_Day": start,
                "class": "CampaignEvent"
            }

    config_builder.add_event(itn_event)