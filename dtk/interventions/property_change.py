def change_node_property(cb, target_property_name, target_property_value, start_day=0, daily_prob=1,
                         max_duration=0, revert=0, nodeIDs=[], node_property_restrictions=[], trigger_condition_list=[],
                         listening_duration=-1):

    node_cfg = {'class': 'NodeSetAll'}
    if nodeIDs:
        node_cfg = {'class': 'NodeSetNodeList',
                    'Node_List': nodeIDs}
    node_property_value_changer =  {
                                   "class": "NodePropertyValueChanger",
                                   "Target_NP_Key_Value": "%s:%s" % (target_property_name, target_property_value),
                                   "Daily_Probability" : daily_prob,
                                   "Maximum_Duration" : max_duration,
                                   "Revert" : revert
                                    }

    if trigger_condition_list:
        changer_event = {
                "class": "CampaignEvent",
                "Start_Day": start_day,
                "Nodeset_Config": node_cfg,
                "Event_Coordinator_Config":
                    {
                        "class": "StandardInterventionDistributionEventCoordinator",
                        "Intervention_Config":
                        {
                                "class": "NodeLevelHealthTriggeredIV",
                                "Blackout_On_First_Occurrence": 1,
                                "Duration": listening_duration,
                                "Trigger_Condition_List": trigger_condition_list,
                                "Actual_IndividualIntervention_Config": node_property_value_changer
                           }
                    }
        }

        if node_property_restrictions:
            changer_event["Event_Coordinator_Config"]["Intervention_Config"]['Node_Property_Restrictions'] = node_property_restrictions

        cb.add_event(changer_event)

    else:
        prop_ch_config = {
                           'class' : 'StandardInterventionDistributionEventCoordinator',
                           "Intervention_Config": node_property_value_changer
                       }

        if node_property_restrictions:
            prop_ch_config['Intervention_Config']['Node_Property_Restrictions'] = node_property_restrictions

        event = {"class": "CampaignEvent",
                 "Start_Day": start_day,
                 "Event_Coordinator_Config": prop_ch_config,
                 "Nodeset_Config": node_cfg}

        cb.add_event(event)


def change_individual_property_at_age(cb, target_property_name, target_property_value, change_age_in_days, start_day=0,
                                      duration=-1, coverage=1, daily_prob=1, max_duration=0, revert=0, nodeIDs=[],
                                      node_property_restrictions=[]):

    actual_config = {
        "class": "PropertyValueChanger",
        "Target_Property_Key": target_property_name,
        "Target_Property_Value": target_property_value,
        "Daily_Probability" : daily_prob,
        "Maximum_Duration" : max_duration,
        "Revert" : revert
    }

    birth_triggered_intervention = {
        "class": "BirthTriggeredIV",
        "Duration": duration,  # default to forever if  duration not specified
        "Demographic_Coverage": coverage,
        "Actual_IndividualIntervention_Config":
            {
                "class": "DelayedIntervention",
                "Coverage": 1,
                "Delay_Distribution": "FIXED_DURATION",
                "Delay_Period": change_age_in_days,
                "Actual_IndividualIntervention_Configs": [actual_config]
            }
    }

    prop_ch_config = { 'class' : 'StandardInterventionDistributionEventCoordinator',
                       "Intervention_Config": birth_triggered_intervention
                   }

    if node_property_restrictions:
        prop_ch_config['Intervention_Config']['Node_Property_Restrictions'] = node_property_restrictions

    node_cfg = {'class' : 'NodeSetAll'}
    if nodeIDs :
        node_cfg = { 'class': 'NodeSetNodeList',
                     'Node_List': nodeIDs}

    event = {"class": "CampaignEvent",
             "Start_Day": start_day,
             "Event_Coordinator_Config": prop_ch_config,
             "Nodeset_Config": node_cfg}

    cb.add_event(event)


def change_individual_property(cb, target_property_name, target_property_value, target='Everyone', start_day=0,
                               coverage=1, daily_prob=1, max_duration=0, revert=0, nodeIDs=[],
                               node_property_restrictions=[], ind_property_restrictions=[], trigger_condition_list=[], listening_duration=-1
                               ):

    node_cfg = {'class': 'NodeSetAll'}
    if nodeIDs:
        node_cfg = {'class': 'NodeSetNodeList',
                    'Node_List': nodeIDs}

    property_value_changer = {
            "class": "PropertyValueChanger",
            "Target_Property_Key": target_property_name,
            "Target_Property_Value": target_property_value,
            "Daily_Probability": daily_prob,
            "Maximum_Duration": max_duration,
            "Revert": revert
        }

    if trigger_condition_list:
         changer_event = {
                "class": "CampaignEvent",
                "Start_Day": start_day,
                "Nodeset_Config": node_cfg,
                "Event_Coordinator_Config":
                    {
                        "class": "StandardInterventionDistributionEventCoordinator",
                        "Intervention_Config":
                        {
                            "class": "NodeLevelHealthTriggeredIV",
                            "Blackout_On_First_Occurrence": 1,
                            "Duration": listening_duration,
                            "Trigger_Condition_List": trigger_condition_list,
                            "Target_Residents_Only": 1,
                            "Demographic_Coverage": coverage,
                            "Actual_IndividualIntervention_Config":property_value_changer
                        }
                    }
         }

         if isinstance(target, dict) and all([k in target.keys() for k in ['agemin', 'agemax']]):
             changer_event["Event_Coordinator_Config"]["Intervention_Config"].update({
                 "Target_Demographic": "ExplicitAgeRanges",
                 "Target_Age_Min": target['agemin'],
                 "Target_Age_Max": target['agemax']})
         else:
             changer_event["Event_Coordinator_Config"]["Intervention_Config"].update({
                 "Target_Demographic": target})  # default is Everyone

         if node_property_restrictions:
             changer_event["Event_Coordinator_Config"]["Intervention_Config"]['Node_Property_Restrictions'] = node_property_restrictions

         if ind_property_restrictions:
             changer_event['Event_Coordinator_Config']['Intervention_Config'][
                 "Property_Restrictions_Within_Node"] = ind_property_restrictions
         cb.add_event(changer_event)


    else:

        prop_ch_config = { 'class' : 'StandardInterventionDistributionEventCoordinator',
                           "Demographic_Coverage": coverage,
                           "Intervention_Config": property_value_changer
                       }

        if isinstance(target, dict) and all([k in target.keys() for k in ['agemin','agemax']]) :
            prop_ch_config.update({
                    "Target_Demographic": "ExplicitAgeRanges",
                    "Target_Age_Min": target['agemin'],
                    "Target_Age_Max": target['agemax'] })
        else :
            prop_ch_config.update({
                    "Target_Demographic": target } ) # default is Everyone

        if node_property_restrictions:
            prop_ch_config['Intervention_Config']['Node_Property_Restrictions'] = node_property_restrictions

        if ind_property_restrictions:
            prop_ch_config['Intervention_Config']["Property_Restrictions_Within_Node"] = ind_property_restrictions

        event = {"class": "CampaignEvent",
                 "Start_Day": start_day,
                 "Event_Coordinator_Config": prop_ch_config,
                 "Nodeset_Config": node_cfg}

        cb.add_event(event)
