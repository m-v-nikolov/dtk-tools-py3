import random


def triggered_campaign_delay_event(config_builder, start,  nodeIDs=[], delay_distribution="FIXED_DURATION",
                                   triggered_campaign_delay=0, trigger_condition_list=[],
                                   listening_duration=-1, event_to_send_out=None, node_property_restrictions=[]):
    if not isinstance(nodeIDs, dict):
        if nodeIDs:
            nodeIDs = {'class': 'NodeSetNodeList',
                    'Node_List': nodeIDs}
        else:
            nodeIDs = {'class': 'NodeSetAll'}

    if not event_to_send_out:
        event_to_send_out = 'Random_Event_%d' % random.randrange(100000)

    event_cfg = {
        "class": "BroadcastEvent",
        "Broadcast_Event": event_to_send_out
    }

    if triggered_campaign_delay :
        intervention = {
            "class": "DelayedIntervention",
            "Delay_Distribution": delay_distribution,
            "Delay_Period": triggered_campaign_delay,
            "Actual_IndividualIntervention_Configs":  [ event_cfg ]
        }
    else :
        intervention = event_cfg

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
                               "Node_Property_Restrictions": node_property_restrictions,
                               "Actual_IndividualIntervention_Config": intervention
                           }
                       }
                       }
    config_builder.add_event(triggered_delay)
    return event_to_send_out
