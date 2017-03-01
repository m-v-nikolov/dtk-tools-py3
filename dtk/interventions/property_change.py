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