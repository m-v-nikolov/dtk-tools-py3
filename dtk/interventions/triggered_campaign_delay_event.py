import random


def triggered_campaign_delay_event(config_builder, start,  nodeIDs=[], triggered_campaign_delay=0,
                                   trigger_condition_list=[], listening_duration=-1, event_to_send_out=None):
    if not isinstance(nodeIDs, dict):
        if nodeIDs:
            nodeIDs = {'class': 'NodeSetNodeList',
                    'Node_List': nodeIDs}
        else:
            nodeIDs = {'class': 'NodeSetAll'}

    if not event_to_send_out:
        event_to_send_out = random.randrange(100000)

    triggered_delay = {"class": "CampaignEvent",
                       "Start_Day": int(start),
                       "Nodeset_Config": nodeIDs,
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
                                               "Broadcast_Event": str(event_to_send_out)
                                           }
                                       ]
                               }
                           }
                       }
                       }
    config_builder.add_event(triggered_delay)
    return event_to_send_out
