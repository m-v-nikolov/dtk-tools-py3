# Bednet parameters
itn_bednet = { "class": "SimpleBednet",
               "Bednet_Type": "ITN", 
               "Blocking_Rate": 0.9,
               "Killing_Rate": 0.6, 
               "Durability_Time_Profile": "DECAYDURABILITY", 
               "Primary_Decay_Time_Constant":   4 * 365,   # killing
               "Secondary_Decay_Time_Constant": 2 * 365,   # blocking
               "Cost_To_Consumer": 3.75
}

def add_ITN(config_builder, start, coverage_by_ages, waning={}, cost=None, nodeIDs=[], perfect=False):
    """
    Add an ITN intervention to the config_builder passed.

    :param config_builder: The :py:class:`DTKConfigBuilder <dtk.utils.core.DTKConfigBuilder>` holding the campaign that will receive the ITN event
    :param start: The start day of the bednet distribution
    :param coverage_by_ages: a list of dictionaries defining the coverage per age group
    :param waning: a dictionary defining the durability of the nets. if empty the default ``DECAYDURABILITY`` with 4 years primary and 2 years secondary will be used.
    :param cost: Set the ``Cost_To_Consumer`` parameter
    :param nodeIDs: If empty, all nodes will get the intervention. If set, only the nodeIDs specified will receive the intervention.
    :return: Nothing
    """
    receiving_itn_event = {
        "class": "BroadcastEvent",
        "Broadcast_Event": "Received_ITN"
    }

    if waning:
        itn_bednet.update({ "Durability_Time_Profile":       waning['profile'], 
                            "Primary_Decay_Time_Constant":   waning['kill'] * 365,
                            "Secondary_Decay_Time_Constant": waning['block'] * 365 })

    if perfect :
        itn_bednet.update({ "Blocking_Rate": 1.0,
                            "Killing_Rate": 1.0, 
                            "Durability_Time_Profile": "BOXDURABILITY", 
                            "Primary_Decay_Time_Constant":   400 * 365,   # killing
                            "Secondary_Decay_Time_Constant": 400 * 365    # blocking
                            })
    if cost:
        itn_bednet['Cost_To_Consumer'] = cost

    itn_bednet_w_event = {
        "Intervention_List" : [itn_bednet, receiving_itn_event] ,
        "class" : "MultiInterventionDistributor"
        }   

    for coverage_by_age in coverage_by_ages:

        ITN_event = { "class" : "CampaignEvent",
                      "Start_Day": start,
                      "Event_Coordinator_Config": {
                          "class": "StandardInterventionDistributionEventCoordinator",
                          "Target_Residents_Only" : 1,
                          "Demographic_Coverage": coverage_by_age["coverage"],
                          "Intervention_Config": itn_bednet_w_event #itn_bednet
                      }
                    }

        if all([k in coverage_by_age.keys() for k in ['min','max']]):
            ITN_event["Event_Coordinator_Config"].update({
                   "Target_Demographic": "ExplicitAgeRanges",
                   "Target_Age_Min": coverage_by_age["min"],
                   "Target_Age_Max": coverage_by_age["max"]})

        if not nodeIDs:
            ITN_event["Nodeset_Config"] = { "class": "NodeSetAll" }
        else:
            ITN_event["Nodeset_Config"] = { "class": "NodeSetNodeList", "Node_List": nodeIDs }

        if 'birth' in coverage_by_age.keys() and coverage_by_age['birth']:
            birth_triggered_intervention = {
                "class": "BirthTriggeredIV",
                "Duration": -1, # forever.  could expire and redistribute every year with different coverage values
                "Demographic_Coverage": coverage_by_age["coverage"],
                "Actual_IndividualIntervention_Config": itn_bednet_w_event #itn_bednet
            }
            ITN_event["Event_Coordinator_Config"]["Intervention_Config"] = birth_triggered_intervention
            ITN_event["Event_Coordinator_Config"].pop("Demographic_Coverage")

        config_builder.add_event(ITN_event)