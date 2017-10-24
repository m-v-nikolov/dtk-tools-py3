import random


def triggered_campaign_delay_event(config_builder, start,  nodeIDs=[], triggered_campaign_delay=0, trigger_condition_list=[], listening_duration=-1):
    node_cfg = {'class': 'NodeSetAll'}
    if nodeIDs:
        node_cfg = {'class': 'NodeSetNodeList',
                    'Node_List': nodeIDs}

    triggered_campaign_delay_trigger = random.randrange(100000)
    triggered_delay = {"class": "CampaignEvent",
                       "Start_Day": int(start),
                       "Nodeset_Config": node_cfg,
                       "Event_Coordinator_Config": {
                           "class": "StandardInterventionDistributionEventCoordinator",
                           "Intervention_Config": {
                               "class": "NodeLevelHealthTriggeredIV",
                               "Trigger_Condition_List": trigger_condition_list,
                               "Duration": listening_duration,
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
    config_builder.add_event(triggered_delay)
    return triggered_campaign_delay_trigger
