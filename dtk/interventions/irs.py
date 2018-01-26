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
import copy, random
from dtk.interventions.triggered_campaign_delay_event import triggered_campaign_delay_event

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


def add_IRS(config_builder, start, coverage_by_ages, cost=None, nodeIDs=[],
            initial_killing=0.5, duration=90, waning={}, node_property_restrictions=[],
            ind_property_restrictions=[], triggered_campaign_delay=0, trigger_condition_list=[], listening_duration=-1):
    """
    Add an IRS intervention to the config_builder passed.
    Please note that using trigger_condition_list does not work for birth-triggered ("birth" in coverage_by_ages).
    when using trigger_condition_list, the "birth" option will be ignored.
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
    :param triggered_campaign_delay: how many time steps after receiving the trigger will the campaign start.
    Eligibility of people or nodes for campaign is evaluated on the start day, not the triggered day.
    :param trigger_condition_list: when not empty,  the start day is the day to start listening for the trigger conditions listed, distributing the spraying
        when the trigger is heard. This does not distribute the BirthTriggered intervention.
    :param listening_duration: how long the distributed event will listen for the trigger for, default is -1, which is indefinitely
    :return: Nothing
    """
    
    receiving_irs_event = {
        "class": "BroadcastEvent",
        "Broadcast_Event": "Received_IRS"
    }

    irs_housingmod['Killing_Config']['Initial_Effect'] = initial_killing
    irs_housingmod['Killing_Config']['Decay_Time_Constant'] = duration

    if waning:
        for cfg in waning :
            irs_housingmod[cfg].update(waning[cfg])

    if cost:
        irs_housingmod['Cost_To_Consumer'] = cost

    irs_housingmod_w_event = {
        "Intervention_List" : [irs_housingmod, receiving_irs_event] ,
        "class" : "MultiInterventionDistributor"
        }

    nodeset_config = {"class": "NodeSetAll"} if not nodeIDs else {"class": "NodeSetNodeList", "Node_List": nodeIDs}

    if triggered_campaign_delay :
        trigger_condition_list = [triggered_campaign_delay_event(config_builder, start, nodeIDs,
                                                                 triggered_campaign_delay,
                                                                 trigger_condition_list,
                                                                 listening_duration)]

    for coverage_by_age in coverage_by_ages:
        if trigger_condition_list:
            if 'birth' not in coverage_by_age.keys():
                IRS_event = {"class": "CampaignEvent",
                             "Start_Day": int(start),
                             "Nodeset_Config": nodeset_config,
                             "Event_Coordinator_Config": {
                                 "class": "StandardInterventionDistributionEventCoordinator",
                                 "Intervention_Config":{
                                     "class": "NodeLevelHealthTriggeredIV",
                                     "Trigger_Condition_List": trigger_condition_list,
                                     "Duration": listening_duration,
                                     "Property_Restrictions_Within_Node": ind_property_restrictions,
                                     "Node_Property_Restrictions": node_property_restrictions,
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

                config_builder.add_event(IRS_event)

        else:
            IRS_event = {"class": "CampaignEvent",
                         "Start_Day": int(start),
                         "Nodeset_Config": nodeset_config,
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

def add_node_IRS(config_builder, start, initial_killing=0.5, box_duration=90,
                 waning_effect_type='WaningEffectExponential', cost=None,
                 irs_ineligibility_duration=0, nodeIDs=[], node_property_restrictions=[],
                 triggered_campaign_delay=0,trigger_condition_list=[], listening_duration=-1):

    irs_config = copy.deepcopy(node_irs_config)
    irs_config['Killing_Config']['class'] = waning_effect_type
    irs_config['Killing_Config']['Initial_Effect'] = initial_killing
    irs_config['Killing_Config']['Decay_Time_Constant'] = box_duration
    if waning_effect_type == 'WaningEffectBox' :
        irs_config['Killing_Config']['Box_Duration'] = box_duration
        del irs_config['Killing_Config']['Decay_Time_Constant']

    if not nodeIDs:
        nodeset_config = {"class": "NodeSetAll"}
    else:
        nodeset_config = {"class": "NodeSetNodeList", "Node_List": nodeIDs}

    if cost:
        node_irs_config['Cost_To_Consumer'] = cost
    node_sprayed_event = {
                           "class": "BroadcastEvent",
                           "Broadcast_Event": "Node_Sprayed"
                         }

    IRS_event = {
                 "class": "CampaignEvent",
                 "Start_Day": int(start),
                 "Nodeset_Config" : nodeset_config,
                 "Event_Coordinator_Config": {
                     "class": "StandardInterventionDistributionEventCoordinator",
                     'Node_Property_Restrictions': node_property_restrictions,
                     "Intervention_Config": {
                        "Intervention_List" : [irs_config,
                                               node_sprayed_event
                                               ] ,
                        "class" : "MultiInterventionDistributor"
                        }
                 },
                 "Event_Name": "Node Level IRS"
                 }

    if trigger_condition_list:
        if triggered_campaign_delay:
            trigger_condition_list = [str(triggered_campaign_delay_event(config_builder, start, nodeIDs,
                                                                         triggered_campaign_delay,
                                                                         trigger_condition_list,
                                                                         listening_duration))]
        IRS_event['Event_Coordinator_Config']['Intervention_Config'] = {
            "class": "NodeLevelHealthTriggeredIV",
            "Blackout_On_First_Occurrence": 1,
            "Blackout_Event_Trigger": "IRS_Blackout_%d" % random.randint(0, 10000),
            "Blackout_Period": 1,
            'Node_Property_Restrictions': node_property_restrictions,
            "Duration": listening_duration,
            "Trigger_Condition_List": trigger_condition_list,
            "Actual_IndividualIntervention_Config": {
                        "Intervention_List" : [irs_config,
                                               node_sprayed_event
                                               ] ,
                        "class" : "MultiInterventionDistributor"
                        },
            "Target_Residents_Only": 1
        }
        del IRS_event['Event_Coordinator_Config']['Node_Property_Restrictions']

    IRS_cfg = copy.copy(IRS_event)
    if irs_ineligibility_duration > 0:
        recent_irs = {"class": "NodePropertyValueChanger",
                      "Target_NP_Key_Value": "SprayStatus:RecentSpray",
                      "Daily_Probability": 1.0,
                      "Maximum_Duration": 0,
                      'Revert': irs_ineligibility_duration
                      }
        if trigger_condition_list:
            IRS_cfg['Event_Coordinator_Config']['Intervention_Config']['Actual_IndividualIntervention_Config']["Intervention_List"].append(recent_irs)
            if not node_property_restrictions :
                IRS_cfg['Event_Coordinator_Config']['Intervention_Config']['Node_Property_Restrictions'] = [{'SprayStatus': 'None'}]
            else :
                for n, np in enumerate(node_property_restrictions) :
                    node_property_restrictions[n]['SprayStatus'] = 'None'
                IRS_cfg['Event_Coordinator_Config']['Intervention_Config']['Node_Property_Restrictions'] = node_property_restrictions
        else:
            IRS_cfg['Event_Coordinator_Config']['Intervention_Config']['Intervention_List'].append(recent_irs)
            if not node_property_restrictions :
                IRS_cfg['Event_Coordinator_Config']['Node_Property_Restrictions'] = [{'SprayStatus': 'None'}]
            else :
                for n, np in enumerate(node_property_restrictions) :
                    node_property_restrictions[n]['SprayStatus'] = 'None'
                IRS_cfg['Event_Coordinator_Config']['Node_Property_Restrictions'] = node_property_restrictions

    config_builder.add_event(IRS_cfg)
