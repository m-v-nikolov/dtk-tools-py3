import copy

''' OLD
# IRS parameters
irs_housingmod = {"class": "IRSHousingModification",
                  "Blocking_Rate": 0.0,  # i.e. repellency
                  "Killing_Rate": 0.7,
                  "Durability_Time_Profile": "DECAYDURABILITY",
                  "Primary_Decay_Time_Constant": 365,  # killing
                  "Secondary_Decay_Time_Constant": 365,  # blocking
                  "Cost_To_Consumer": 8.0
                  }
'''
import copy

irs_housingmod = { "class": "IRSHousingModification",
                "Killing_Config": {
                    "Initial_Effect": 0.5,
                    "Decay_Time_Constant": 90,
                    "class": "WaningEffectExponential"
                },
                "Blocking_Config": {
                    "Initial_Effect": 0.0,
                    "Decay_Time_Constant": 730,
                    "class": "WaningEffectExponential"
                },
               "Cost_To_Consumer": 8.0
}

node_irs_config = { "Reduction_Config": {
                        "Decay_Time_Constant": 365, 
                        "Initial_Effect": 0, 
                        "class": "WaningEffectExponential"
                    }, 
                    "Cost_To_Consumer": 1.0, 
                    "Habitat_Target": "ALL_HABITATS", 
                    "Killing_Config": {
                        "Decay_Time_Constant": 90, 
                        "Initial_Effect": 0.5, 
                        "class": "WaningEffectExponential"
                    }, 
                    "Spray_Kill_Target": "SpaceSpray_Indoor", 
                    "class": "SpaceSpraying"
                }

node_sprayed_event = {
    "class": "BroadcastEvent",
    "Broadcast_Event": "Node_Sprayed"
    }

def add_IRS(config_builder, start, coverage_by_ages, waning={}, cost=None, nodeIDs=[]):
    """
    Add an IRS intervention to the config_builder passed.

    :param config_builder: The :py:class:`DTKConfigBuilder <dtk.utils.core.DTKConfigBuilder>` holding the campaign that will receive the IRS event
    :param start: The start day of the spraying
    :param coverage_by_ages: a list of dictionaries defining the coverage per age group
    :param waning: a dictionary defining the durability of the nets. if empty the default ``DECAYDURABILITY`` with 1 year primary and 1 year secondary will be used.
    :param cost: Set the ``Cost_To_Consumer`` parameter
    :param nodeIDs: If empty, all nodes will get the intervention. If set, only the nodeIDs specified will receive the intervention.
    :return: Nothing
    """
    
    receiving_irs_event = {
        "class": "BroadcastEvent",
        "Broadcast_Event": "Received_IRS"
    }

    if waning:
        irs_housingmod.update({ "Durability_Time_Profile":   waning['profile'], 
                            "Primary_Decay_Time_Constant":   waning['kill'] * 365,
                            "Secondary_Decay_Time_Constant": waning['block'] * 365 })

    if cost:
        irs_housingmod['Cost_To_Consumer'] = cost

    irs_housingmod_w_event = {
        "Intervention_List" : [irs_housingmod, receiving_irs_event] ,
        "class" : "MultiInterventionDistributor"
        }

    for coverage_by_age in coverage_by_ages:
        

        IRS_event = {"class": "CampaignEvent",
                     "Start_Day": int(start),
                     "Event_Coordinator_Config": {
                         "class": "StandardInterventionDistributionEventCoordinator",
                         "Demographic_Coverage": coverage_by_age["coverage"],
                         "Target_Residents_Only": 1,
                         "Intervention_Config": irs_housingmod_w_event
                     }
                     }

        if all([k in coverage_by_age.keys() for k in ['min', 'max']]):
            IRS_event["Event_Coordinator_Config"].update({
                "Target_Demographic": "ExplicitAgeRanges",
                "Target_Age_Min": coverage_by_age["min"],
                "Target_Age_Max": coverage_by_age["max"]})

        if not nodeIDs:
            IRS_event["Nodeset_Config"] = {"class": "NodeSetAll"}
        else:
            IRS_event["Nodeset_Config"] = {"class": "NodeSetNodeList", "Node_List": nodeIDs}

        if 'birth' in coverage_by_age.keys() and coverage_by_age['birth']:
            birth_triggered_intervention = {
            "class": "BirthTriggeredIV",
            "Duration": coverage_by_age.get('duration', -1), # default to forever if duration not specified
            "Demographic_Coverage": coverage_by_age["coverage"],
            "Actual_IndividualIntervention_Config": irs_housingmod
            }

            IRS_event["Event_Coordinator_Config"]["Intervention_Config"] = birth_triggered_intervention
            IRS_event["Event_Coordinator_Config"].pop("Demographic_Coverage")

        config_builder.add_event(IRS_event)

def add_node_IRS(config_builder, start, coverage=1.0, initial_killing=0.7, box_duration=365, cost=None, nodeIDs=[]):

    irs_config = copy.deepcopy(node_irs_config)
    irs_config['Killing_Config']['Box_Duration'] = box_duration
    irs_config['Killing_Config']['Initial_Effect'] = initial_killing

    if cost:
        node_irs_config['Cost_To_Consumer'] = cost

    IRS_event = {   "Event_Coordinator_Config": {
                        "Intervention_Config": irs_config, 
                        "class": "NodeEventCoordinator"
                    }, 
                    "Nodeset_Config": {
                        "class": "NodeSetAll"
                    }, 
                    "Start_Day": int(start), 
                    "Event_Name": "Node Level IRS",
                    "class": "CampaignEvent"
                }

    if not nodeIDs:
        IRS_event["Nodeset_Config"] = { "class": "NodeSetAll" }
    else:
        import random
        nodeIDs = [x for x in nodeIDs if random.random() <= coverage]
        if nodeIDs == [] : # no nodes were sprayed
            return
        IRS_event["Nodeset_Config"] = { "class": "NodeSetNodeList", "Node_List": nodeIDs }

    config_builder.add_event(IRS_event)

def add_reactive_node_IRS(config_builder, start, duration=10000, trigger_coverage=1.0, irs_coverage=1.0, node_selection_type='DISTANCE_ONLY', 
                          reactive_radius=0, blackout_duration=60, delay=7, nodes={"class": "NodeSetAll"}) :

    irs_trigger_config = fmda_cfg(reactive_radius, node_selection_type, 'Spray_IRS')

    trigger_irs = {   "Event_Name": "Trigger Reactive IRS", 
                    "class": "CampaignEvent",
                    "Start_Day": start,
                    "Event_Coordinator_Config": 
                    {
                        "class": "StandardInterventionDistributionEventCoordinator",
                        "Intervention_Config" : { 
                            "class": "NodeLevelHealthTriggeredIV",
                            "Demographic_Coverage": trigger_coverage,
                            "Trigger_Condition": "TriggerString",
                            "Trigger_Condition_String": "Received_Treatment", # triggered by successful health-seeking
                            "Duration" : duration,
                            "Actual_IndividualIntervention_Config" : { 
                                "class": "DelayedIntervention",                    
                                "Delay_Distribution": "FIXED_DURATION",
                                "Delay_Period": delay,
                                "Actual_IndividualIntervention_Configs" : [irs_trigger_config]
                                }
                        }
                    },
                    "Nodeset_Config": nodes}


    distribute_irs = {   "Event_Name": "Distribute IRS", 
                                "class": "CampaignEvent",
                                "Start_Day": start,
                                "Event_Coordinator_Config": 
                                {
                                    "class": "StandardInterventionDistributionEventCoordinator",
                                    "Intervention_Config" : { 
                                        "class": "NodeLevelHealthTriggeredIV",
                                        "Demographic_Coverage": irs_coverage,
                                        "Trigger_Condition": "TriggerString",
                                        "Trigger_Condition_String": "Spray_IRS",
                                        "Blackout_Event_Trigger" : "IRS_Blackout",
                                        "Blackout_Period" : blackout_duration,
                                        "Blackout_On_First_Occurrence" : 1,
                                        "Actual_IndividualIntervention_Config" : {
                                                "Intervention_List" : [node_irs_config, node_sprayed_event],
                                                "class" : "MultiInterventionDistributor"
                                            }
                                    }
                                },
                                "Nodeset_Config": nodes
                            }


    config_builder.add_event(trigger_irs)
    config_builder.add_event(distribute_irs)
    