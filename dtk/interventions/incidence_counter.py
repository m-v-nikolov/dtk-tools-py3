def add_incidence_counter(cb,
                          start_day=0,
                          count_duration=365,
                          count_triggers=['NewClinicalCase', 'NewSevereCase'],
                          threshold_type='COUNT',
                          thresholds=[10, 100],
                          triggered_events=['Action1', 'Action2'],
                          coverage=1,
                          repetitions=1,
                          tsteps_btwn_repetitions=365,
                          target_group='Everyone',
                          nodeIDs=[],
                          node_property_restrictions=[],
                          ind_property_restrictions=[]
                          ):
    """
    Add an intervention to

    :param cb: The :py:class:`DTKConfigBuilder <dtk.utils.core.DTKConfigBuilder>` that will receive the risk-changing
    intervention.
    :param start_day: date upon which to change biting risk
    :param repetitions: Number of repetitions
    :param tsteps_btwn_repetitions: days between repetitions
    :param count_duration: how long to monitor for
    :param count_triggers: which events increment the monitor's count
    :param threshold_type: 'COUNT' for raw counts or 'PERCENTAGE' to normalize by population
    :param thresholds: thresholds at which to engage a response
    :param triggered_events: event name to broadcast upon surpassing thresholds. Needs one per threshold.
    :param coverage: Demographic coverage of the monitoring. Affects probability a count_trigger will be counted but is
    ignored for calculating denominator for PERCENTAGE.
    :param target_group: to restrict monitoring by age, dict of {'agemin' : x, 'agemax' : y}. Default is targeting
    everyone.
    :param nodeIDs: list of node IDs to monitor; if empty, defaults to all nodes
    :param ind_property_restrictions: used with Property_Restrictions_Within_Node. Format: list of dicts:
    [{ "IndividualProperty1" : "PropertyValue1" }, {'IndividualProperty2': "PropertyValue2"}, ...]
    :param node_property_restrictions: used with NodePropertyRestrictions.
    Format: list of dicts: [{ "NodeProperty1" : "PropertyValue1" }, {'NodeProperty2': "PropertyValue2"}, ...]

    """

    counter_config = {
        'Count_Events_For_Num_Timesteps' : count_duration,
        'Trigger_Condition_List' : count_triggers,
        "Target_Demographic": "Everyone",
        "Demographic_Coverage": coverage
    }
    responder_config = {
        'Threshold_Type' : threshold_type,
        'Action_List' : [ { 'Threshold' : t, 'Event_To_Broadcast' : e} for t,e in zip(thresholds, triggered_events)]
    }

    if target_group != 'Everyone':
        counter_config.update({
            "Target_Demographic": "ExplicitAgeRanges",  # Otherwise default is Everyone
            "Target_Age_Min": target_group['agemin'],
            "Target_Age_Max": target_group['agemax']
        })

    if node_property_restrictions:
        counter_config['Node_Property_Restrictions'] = node_property_restrictions

    if ind_property_restrictions:
        counter_config["Property_Restrictions_Within_Node"] = ind_property_restrictions

    monitoring_event = {
        "class": "CampaignEvent",
        "Start_Day": start_day,
        "Nodeset_Config": {
            "class": "NodeSetAll"
        },
        "Event_Coordinator_Config": {
            "class": "IncidenceEventCoordinator",
            "Number_Repetitions": repetitions,
            "Timesteps_Between_Repetitions": tsteps_btwn_repetitions,
            "Incidence_Counter": counter_config,
            "Responder" : responder_config
        }
    }

    if not nodeIDs:
        monitoring_event["Nodeset_Config"] = {"class": "NodeSetAll"}
    else:
        monitoring_event["Nodeset_Config"] = {"class": "NodeSetNodeList", "Node_List": nodeIDs}

    cb.add_event(monitoring_event)
    listed_events = cb.get_param('Listed_Events')
    new_events = [x for x in triggered_events if x not in listed_events]
    cb.update_params({'Listed_Events': listed_events + new_events})
