import copy

# new campaign format : need to fix some add_itn() functionalities
itn_bednet = { "class": "SimpleBednet",
               "Bednet_Type": "ITN", 
               "Killing_Config": {
                    "Initial_Effect": 0.6,
                    "Decay_Time_Constant": 1460,
                    "class": "WaningEffectExponential"
                },
               "Blocking_Config": {
                    "Initial_Effect": 0.9,
                    "Decay_Time_Constant": 730,
                    "class": "WaningEffectExponential"
                },
               "Usage_Config": {
                   "Expected_Discard_Time": 3650, # default: keep nets for 10 years
                   "Initial_Effect": 1.0,
                   "class": "WaningEffectRandomBox"
               },
               "Cost_To_Consumer": 3.75
}

receiving_itn_event = {
    "class": "BroadcastEvent",
    "Broadcast_Event": "Received_ITN"
}


def add_ITN(config_builder, start, coverage_by_ages, waning={}, cost=None, nodeIDs=[], node_property_restrictions=[],
            ind_property_restrictions=[], trigger_string=''):
    """
    Add an ITN intervention to the config_builder passed.
    :param config_builder: The :py:class:`DTKConfigBuilder <dtk.utils.core.DTKConfigBuilder>` holding the campaign that will receive the ITN event
    :param start: The start day of the bednet distribution
    :param coverage_by_ages: a list of dictionaries defining the coverage per age group
    :param waning: a dictionary defining the durability of the nets. if empty the default decay profile will be used.
    For example, update usage duration to 180 days as waning={'Usage_Config' : {"Expected_Discard_Time": 180}}
    :param cost: Set the ``Cost_To_Consumer`` parameter
    :param nodeIDs: If empty, all nodes will get the intervention. If set, only the nodeIDs specified will receive the intervention.
    :return: Nothing
    """

    if waning:
        for cfg in waning :
            itn_bednet[cfg].update(waning[cfg])

    if cost:
        itn_bednet['Cost_To_Consumer'] = cost

    itn_bednet_w_event = {
        "Intervention_List" : [itn_bednet, receiving_itn_event] ,
        "class" : "MultiInterventionDistributor"
        }   

    for coverage_by_age in coverage_by_ages:

        ITN_event = {"class": "CampaignEvent",
                     "Start_Day": int(start),
                     "Event_Coordinator_Config": {
                         "class": "StandardInterventionDistributionEventCoordinator",
                         'Node_Property_Restrictions': []
                         }
                     }

        if trigger_string:
            ITN_event['Event_Coordinator_Config']['Intervention_Config'] = {
                "class" : "NodeLevelHealthTriggeredIV",
                "Trigger_Condition_List": [trigger_string],
                "Target_Residents_Only": 1,
                "Demographic_Coverage": coverage_by_age["coverage"],
                "Actual_IndividualIntervention_Config" : itn_bednet_w_event
            }

        else :
            ITN_event['Event_Coordinator_Config'].update( {
                "Target_Residents_Only": 1,
                "Demographic_Coverage": coverage_by_age["coverage"],
                'Intervention_Config' : itn_bednet_w_event
            })

        if node_property_restrictions:
            ITN_event['Event_Coordinator_Config']['Node_Property_Restrictions'].extend(node_property_restrictions)

        if all([k in coverage_by_age.keys() for k in ['min','max']]):
            target_by_age = {
                   "Target_Demographic": "ExplicitAgeRanges",
                   "Target_Age_Min": coverage_by_age["min"],
                   "Target_Age_Max": coverage_by_age["max"]}
            if trigger_string :
                ITN_event["Event_Coordinator_Config"]['Intervention_Config'].update(target_by_age)
            else :
                ITN_event["Event_Coordinator_Config"].update(target_by_age)

        if not nodeIDs:
            ITN_event["Nodeset_Config"] = { "class": "NodeSetAll" }
        else:
            ITN_event["Nodeset_Config"] = { "class": "NodeSetNodeList", "Node_List": nodeIDs }

        if 'birth' in coverage_by_age.keys() and coverage_by_age['birth']:
            birth_triggered_intervention = {
                "class": "BirthTriggeredIV",
                "Duration": coverage_by_age.get('duration', -1), # default to forever if  duration not specified
                "Demographic_Coverage": coverage_by_age["coverage"],
                "Actual_IndividualIntervention_Config": itn_bednet_w_event #itn_bednet
            }

            ITN_event["Event_Coordinator_Config"]["Intervention_Config"] = birth_triggered_intervention
            ITN_event["Event_Coordinator_Config"].pop("Demographic_Coverage")
            ITN_event["Event_Coordinator_Config"].pop("Target_Residents_Only")

            if ind_property_restrictions:
                ITN_event["Event_Coordinator_Config"]["Intervention_Config"]["Property_Restrictions_Within_Node"] = ind_property_restrictions

        elif ind_property_restrictions:
            if trigger_string :
                ITN_event["Event_Coordinator_Config"]['Intervention_Config']["Property_Restrictions_Within_Node"] = ind_property_restrictions
            else :
                ITN_event["Event_Coordinator_Config"]["Property_Restrictions_Within_Node"] = ind_property_restrictions

        config_builder.add_event(ITN_event)
