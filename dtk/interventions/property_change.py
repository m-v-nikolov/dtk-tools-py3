def change_node_property(cb, target_property_name, target_property_value, start_day=0, daily_prob=1,
                         max_duration=0, revert=0, nodeIDs=[], node_property_restrictions=[]):

    prop_ch_config = { 'class' : 'StandardInterventionDistributionEventCoordinator',
                       "Intervention_Config":
                       {
                           "class": "NodePropertyValueChanger",
                           "Target_NP_Key_Value": "%s:%s" % (target_property_name, target_property_value),
                           "Daily_Probability" : daily_prob,
                           "Maximum_Duration" : max_duration,
                           "Revert" : revert
                       }
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
                               node_property_restrictions=[]
                               ):

    actual_config = {
        "class": "PropertyValueChanger",
        "Target_Property_Key": target_property_name,
        "Target_Property_Value": target_property_value,
        "Daily_Probability" : daily_prob,
        "Maximum_Duration" : max_duration,
        "Revert" : revert
    }

    prop_ch_config = { 'class' : 'StandardInterventionDistributionEventCoordinator',
                       "Demographic_Coverage": coverage,
                       "Intervention_Config": actual_config
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

    node_cfg = {'class' : 'NodeSetAll'}
    if nodeIDs :
        node_cfg = { 'class': 'NodeSetNodeList',
                     'Node_List': nodeIDs}

    event = {"class": "CampaignEvent",
             "Start_Day": start_day,
             "Event_Coordinator_Config": prop_ch_config,
             "Nodeset_Config": node_cfg}

    cb.add_event(event)
