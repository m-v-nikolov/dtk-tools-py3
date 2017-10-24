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
import random

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


def add_IRS(config_builder, start, coverage_by_ages, cost=1, nodeIDs=[],
            initial_killing=0.5, duration=90, waning={}, ind_property_restrictions=[], node_property_restrictions=[],
            triggered_campaign_delay=0, trigger_condition_list=[], listening_duration=-1):
    """
    Add an IRS intervention to the config_builder passed.
    Please note that using trigger_condition_list is mutually exclusive with birthtriggered irs.

    :param config_builder: The :py:class:`DTKConfigBuilder <dtk.utils.core.DTKConfigBuilder>` holding the campaign that will receive the IRS event
    :param start: The start day of the spraying
    :param coverage_by_ages: a list of dictionaries defining the coverage per age group or birth-triggered intervention
    [{"coverage":1,"min": 1, "max": 10},{"coverage":1,"min": 11, "max": 50},{ "coverage":0.5, "birth":"birth", "duration":34}]
    :param cost: Set the ``Cost_To_Consumer`` parameter
    :param nodeIDs: If empty, all nodes will get the intervention. If set, only the nodeIDs specified will receive the intervention.
    :param initial_killing: sets Initial Effect within the killing config
    :param duration: sets the Decal_Time_Constant within the killing config
    :param waning: a dictionary defining the durability of the nets. if empty the default ``DECAYDURABILITY`` with 1 year primary and 1 year secondary will be used.
    :param ind_property_restrictions: Restricts irs based on list of individual properties in format [{"BitingRisk":"High"}, {"IsCool":"Yes}]
    :param node_property_restrictions: restricts irs based on list of node properties in format [{"Place":"RURAL"}, {"ByALake":"Yes}]
    :param trigger_condition_list: when not empty,  the start day is the day to start listening for the trigger conditions listed, distributing the spraying
        when the trigger is heard. This does not distribute the BirthTriggered intervention.
    :param listening_duration: how long the distributed event will listen for the trigger for, default is -1, which is indefinitely
    :return: Nothing
    """
    
    receiving_irs_event = {
        "class": "BroadcastEvent",
        "Broadcast_Event": "Received_IRS"
    }

    # no "if" needed since it's always defined
    irs_housingmod['Killing_Config']['Initial_Effect'] = initial_killing
    irs_housingmod['Killing_Config']['Decay_Time_Constant'] = duration
    irs_housingmod['Cost_To_Consumer'] = cost

    if waning:
        for cfg in waning :
            irs_housingmod[cfg].update(waning[cfg])


    irs_housingmod_w_event = {
        "Intervention_List" : [irs_housingmod, receiving_irs_event] ,
        "class" : "MultiInterventionDistributor"
        }

    triggered_campaign_delay_trigger = random.randrange(100000)  # initiating in case there is a campaign delay.
    if triggered_campaign_delay:
        triggered_delay = {"class": "CampaignEvent",
                           "Start_Day": int(start),
                           "Event_Coordinator_Config": {
                               "class": "StandardInterventionDistributionEventCoordinator",
                               "Intervention_Config": {
                                   "class": "NodeLevelHealthTriggeredIV",
                                   "Trigger_Condition_List": trigger_condition_list,
                                   "Duration": listening_duration,
                                   "Node_Property_Restrictions": [],
                                   "Blackout_Event_Trigger": "TBActivation",
                               # we don't care about this, just need something to be here so the blackout works at all
                                   "Blackout_Period": 1,  # so we only distribute the node event(s) once
                                   "Blackout_On_First_Occurrence": 1,
                                   "Target_Residents_Only": 1,
                                   "Actual_IndividualIntervention_Config": {
                                       "class": "DelayedIntervention",
                                       "Delay_Distribution": "FIXED_DURATION",
                                       "Delay_Period": triggered_campaign_delay,
                                       "Actual_IndividualIntervention_Configs":
                                           [
                                               {
                                                   "class": "BroadcastEvent",
                                                   "Broadcast_Event": str(triggered_campaign_delay_trigger)
                                               }
                                           ]
                                   }
                               }
                           }
                           }
        if not nodeIDs:
            triggered_delay["Nodeset_Config"] = {"class": "NodeSetAll"}
        else:
            triggered_delay["Nodeset_Config"] = {"class": "NodeSetNodeList", "Node_List": nodeIDs}

        config_builder.add_event(triggered_delay)

    for coverage_by_age in coverage_by_ages:
        if trigger_condition_list:
            IRS_event = {"class": "CampaignEvent",
                         "Start_Day": int(start),
                         "Event_Coordinator_Config": {
                             "class": "StandardInterventionDistributionEventCoordinator",
                             "Intervention_Config":{
                                 "class": "NodeLevelHealthTriggeredIV",
                                 "Trigger_Condition_List": trigger_condition_list,
                                 "Duration": listening_duration,
                                 "Demographic_Coverage": coverage_by_age["coverage"],
                                 "Target_Residents_Only": 1,
                                 "Actual_IndividualIntervention_Config": irs_housingmod_w_event
                            }
                         }
                        }

            if all([k in coverage_by_age.keys() for k in ['min', 'max']]):
                IRS_event["Event_Coordinator_Config"]["Intervention_Config"].update({
                    "Target_Demographic": "ExplicitAgeRanges",
                    "Target_Age_Min": coverage_by_age["min"],
                    "Target_Age_Max": coverage_by_age["max"]})

            if triggered_campaign_delay:
                IRS_event["Event_Coordinator_Config"]["Intervention_Config"]["Trigger_Condition_List"] = triggered_campaign_delay_trigger

            if not nodeIDs:
                IRS_event["Nodeset_Config"] = {"class": "NodeSetAll"}
            else:
                IRS_event["Nodeset_Config"] = {"class": "NodeSetNodeList", "Node_List": nodeIDs}

            if ind_property_restrictions:
                IRS_event["Event_Coordinator_Config"]["Intervention_Config"][
                    "Property_Restrictions_Within_Node"] = ind_property_restrictions

            if node_property_restrictions:
                IRS_event['Event_Coordinator_Config']["Intervention_Config"][
                    'Node_Property_Restrictions'] = node_property_restrictions

            config_builder.add_event(IRS_event)

        else:
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
                    "Actual_IndividualIntervention_Config": irs_housingmod_w_event
                }

                IRS_event["Event_Coordinator_Config"]["Intervention_Config"] = birth_triggered_intervention
                IRS_event["Event_Coordinator_Config"].pop("Demographic_Coverage")
                IRS_event["Event_Coordinator_Config"].pop("Target_Residents_Only")

            if ind_property_restrictions and 'birth' in coverage_by_age.keys() and coverage_by_age['birth']:
                IRS_event["Event_Coordinator_Config"]["Intervention_Config"][
                    "Property_Restrictions_Within_Node"] = ind_property_restrictions
            elif ind_property_restrictions:
                IRS_event["Event_Coordinator_Config"][
                    "Property_Restrictions_Within_Node"] = ind_property_restrictions

            if node_property_restrictions:
                IRS_event['Event_Coordinator_Config'][
                    'Node_Property_Restrictions'] = node_property_restrictions

            config_builder.add_event(IRS_event)


def add_node_IRS(config_builder, start=0, initial_killing=0.5, box_duration=90, cost=1,
                 irs_ineligibility_duration=0, nodeIDs=[], node_property_restrictions=[],
                 triggered_campaign_delay=0, trigger_condition_list=[], listening_duration=-1):
    # when triggered_campaign_delay, the node property restrictions are evaluated at the time of the campaign, not the at the time of the trigger

    irs_config = copy.deepcopy(node_irs_config)
    irs_config['Killing_Config']['Decay_Time_Constant'] = box_duration
    irs_config['Killing_Config']['Initial_Effect'] = initial_killing
    irs_config['Cost_To_Consumer'] = cost

    if trigger_condition_list:
        triggered_campaign_delay_trigger = random.randrange(100000) #initiating in case there is a campaign delay.
        if irs_ineligibility_duration:
            triggered_ineligibility ={"class": "CampaignEvent",
                         "Start_Day": int(start),
                         "Event_Coordinator_Config": {
                             "class": "StandardInterventionDistributionEventCoordinator",
                             "Intervention_Config": {
                                 "class": "NodeLevelHealthTriggeredIV",
                                 "Trigger_Condition_List": trigger_condition_list,
                                 "Duration": listening_duration,
                                 "Node_Property_Restrictions": [],
                                 "Blackout_Event_Trigger": "TBActivation", #we don't care about this, just need something to be here so the blackout works at all
                                 "Blackout_Period": 1, # so we only distribute the node event(s) once
                                 "Blackout_On_First_Occurrence": 1,
                                 "Target_Residents_Only": 1,
                                 "Actual_IndividualIntervention_Config": {
                                      "class": "NodePropertyValueChanger",
                                      "Target_NP_Key_Value": "SprayStatus:RecentSpray",
                                      "Daily_Probability": 1.0,
                                      "Maximum_Duration": 0,
                                      'Revert': irs_ineligibility_duration
                                        }
                                 }
                             }
                         }

            if not nodeIDs:
                triggered_ineligibility["Nodeset_Config"] = { "class": "NodeSetAll" }
            else:
                triggered_ineligibility["Nodeset_Config"] = { "class": "NodeSetNodeList", "Node_List": nodeIDs }

            # adding "AND" SprayStatus: None to all the Node Property Restrictions.
            for item in node_property_restrictions:
                item.update({"SprayStatus": "None"})
            triggered_ineligibility['Event_Coordinator_Config']["Intervention_Config"]['Node_Property_Restrictions'].extend(node_property_restrictions)
            if triggered_campaign_delay:
                triggered_ineligibility["Event_Coordinator_Config"]["Intervention_Config"][
                    "Trigger_Condition_List"] = [str(triggered_campaign_delay_trigger)]  # if delayed, we're waiting for delayed trigger

            config_builder.add_event(triggered_ineligibility)

        if triggered_campaign_delay:
            triggered_delay = {"class": "CampaignEvent",
             "Start_Day": int(start),
             "Event_Coordinator_Config": {
                 "class": "StandardInterventionDistributionEventCoordinator",
                 "Intervention_Config": {
                     "class": "NodeLevelHealthTriggeredIV",
                     "Trigger_Condition_List": trigger_condition_list,
                     "Duration": listening_duration,
                     "Node_Property_Restrictions": [],
                     "Blackout_Event_Trigger": "TBActivation", # we don't care about this, just need something to be here so the blackout works at all
                     "Blackout_Period": 1,  # so we only distribute the node event(s) once
                     "Blackout_On_First_Occurrence": 1,
                     "Target_Residents_Only": 1,
                     "Actual_IndividualIntervention_Config": {
                        "class": "DelayedIntervention",
                        "Delay_Distribution": "FIXED_DURATION",
                        "Delay_Period": triggered_campaign_delay,
                        "Actual_IndividualIntervention_Configs":
                            [
                                {
                                    "class": "BroadcastEvent",
                                    "Broadcast_Event": str(triggered_campaign_delay_trigger)
                                }
                            ]
                     }
                 }
             }
             }
            if not nodeIDs:
                triggered_delay["Nodeset_Config"] = {"class": "NodeSetAll"}
            else:
                triggered_delay["Nodeset_Config"] = {"class": "NodeSetNodeList", "Node_List": nodeIDs}

            config_builder.add_event(triggered_delay)

        IRS_event = {"class": "CampaignEvent",
                     "Start_Day": int(start),
                     "Event_Coordinator_Config": {
                         "class": "StandardInterventionDistributionEventCoordinator",
                         "Intervention_Config": {
                             "class": "NodeLevelHealthTriggeredIV",
                             "Trigger_Condition_List": trigger_condition_list,
                             "Duration": listening_duration,
                             "Node_Property_Restrictions": [],
                             "Blackout_Event_Trigger": "TBActivation", #we don't care about this, just need something to be here so the blackout works at all
                             "Blackout_Period": 1, # so we only distribute the node event(s) once
                             "Blackout_On_First_Occurrence": 1,
                             "Target_Residents_Only": 1,
                             "Actual_IndividualIntervention_Config": irs_config
                         }
                     }
                     }
        if not nodeIDs:
            IRS_event["Nodeset_Config"] = { "class": "NodeSetAll" }
        else:
            IRS_event["Nodeset_Config"] = { "class": "NodeSetNodeList", "Node_List": nodeIDs }

        # if irs_ineligibility, addition restrictions have been added above.
        if node_property_restrictions:
            IRS_event['Event_Coordinator_Config']["Intervention_Config"]['Node_Property_Restrictions'].extend(node_property_restrictions)
        if triggered_campaign_delay:
            IRS_event['Event_Coordinator_Config']["Intervention_Config"]["Trigger_Condition_List"] = [str(triggered_campaign_delay_trigger)] #if delayed, we're waiting for delayed trigger

        config_builder.add_event(IRS_event)

    else:
        IRS_event = {
            "Event_Coordinator_Config": {
                "Intervention_Config": irs_config,
                'Node_Property_Restrictions': [],
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
            IRS_event["Nodeset_Config"] = { "class": "NodeSetNodeList", "Node_List": nodeIDs }

        IRS_cfg = copy.copy(IRS_event)
        if irs_ineligibility_duration > 0:
            recent_irs = {"class": "NodePropertyValueChanger",
                          "Target_NP_Key_Value": "SprayStatus:RecentSpray",
                          "Daily_Probability": 1.0,
                          "Maximum_Duration": 0,
                          'Revert': irs_ineligibility_duration
                          }
            IRS_cfg['Event_Coordinator_Config']['class'] = 'MultiInterventionEventCoordinator'
            IRS_cfg['Event_Coordinator_Config']['Intervention_Configs'] = [
                irs_config,
                recent_irs]
            del IRS_cfg['Event_Coordinator_Config']['Intervention_Config']

            IRS_cfg['Event_Coordinator_Config']['Node_Property_Restrictions'].extend([{ 'SprayStatus' : 'None'}])

        if node_property_restrictions:
            IRS_cfg['Event_Coordinator_Config']['Node_Property_Restrictions'].extend(node_property_restrictions)
        config_builder.add_event(IRS_cfg)

