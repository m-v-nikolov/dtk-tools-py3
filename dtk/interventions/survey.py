
def add_diagnostic_survey(cb, coverage=1, repetitions=1, tsteps_btwn=365, target='Everyone', start_day=0, diagnostic_type='NewDetectionTech', diagnostic_threshold=40, 
                          broadcast_event='', include_my_node=1, node_selection_type='DISTANCE_AND_MIGRATION', max_dist_to_other_nodes_km=1,
                          nodes={"class": "NodeSetAll"}):
    """
    Function to add recurring prevalence surveys with configurable diagnostic

    :param cb: Configuration builder holding the interventions
    :param repetitions: Number of repetitions
    :param tsteps_btwn:  Timesteps between repetitions
    :param target: Target demographic. Default is 'Everyone'
    :param start_day: Start day for the outbreak
    :param coverage: 
    :param diagnostic_type: 
    :param diagnostic_threshold: 
    :param broadcast_event: 
    :param include_my_node: 
    :param node_selection_type: 
    :param max_dist_to_other_nodes_km: 
    :return: A dictionary holding the fraction and the timesteps between events
    """
    survey_event = { "class" : "CampaignEvent",
                                 "Start_Day": start_day,
                                 "Event_Coordinator_Config": {
                                     "class": "StandardInterventionDistributionEventCoordinator",
                                     "Number_Distributions": -1,
                                     "Number_Repetitions": repetitions,
                                     "Timesteps_Between_Repetitions": tsteps_btwn,
                                     "Target_Demographic": target,
                                     "Demographic_Coverage": coverage,
                                     "Intervention_Config": {
                                         "Diagnostic_Type": diagnostic_type, 
                                         "Diagnostic_Threshold": diagnostic_threshold, 
                                         "class": "MalariaDiagnostic",
                                         "Event_Or_Config": "Config",
                                         "Positive_Diagnosis_Config": {
                                             "class": "BroadcastEventToOtherNodes",
                                             "Event_Trigger": broadcast_event,
                                             "Include_My_Node" : include_my_node,
                                             "Node_Selection_Type" : node_selection_type,
                                             "Max_Distance_To_Other_Nodes_Km" : max_dist_to_other_nodes_km
                                             }
                                         }
                                     },
                                 "Nodeset_Config": nodes
                                 }

    cb.add_event(survey_event)
    return
