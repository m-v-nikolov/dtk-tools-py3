def add_diagnostic_survey(cb, coverage=1, repetitions=1, tsteps_btwn=365, target='Everyone', start_day=0, diagnostic_type='NewDetectionTech', diagnostic_threshold=40,
                          nodes={"class": "NodeSetAll"}, positive_diagnosis_config={}):
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

    intervention_cfg = {
                        "Diagnostic_Type": diagnostic_type, 
                        "Detection_Threshold": diagnostic_threshold, 
                        "class": "MalariaDiagnostic"                                          
                        }

    if not positive_diagnosis_config :
        intervention_cfg["Event_Or_Config"] = "Event"
        intervention_cfg["Positive_Diagnosis_Event"] = "TestedPositive"    
    else :
        intervention_cfg["Event_Or_Config"] = "Config"
        intervention_cfg["Positive_Diagnosis_Config"] = positive_diagnosis_config   

    survey_event = { "class" : "CampaignEvent",
                                 "Start_Day": start_day,
                                 "Event_Coordinator_Config": {
                                     "class": "StandardInterventionDistributionEventCoordinator",
                                     "Number_Distributions": -1,
                                     "Number_Repetitions": repetitions,
                                     "Timesteps_Between_Repetitions": tsteps_btwn,
                                     "Demographic_Coverage": coverage,
                                     "Intervention_Config": intervention_cfg
                                     },
                                 "Nodeset_Config": nodes
                                 }

    if isinstance(target, dict) and all([k in target.keys() for k in ['agemin','agemax']]) :
        survey_event["Event_Coordinator_Config"].update({
                "Target_Demographic": "ExplicitAgeRanges", 
                "Target_Age_Min": target['agemin'],
                "Target_Age_Max": target['agemax'] })
    else :
        survey_event["Event_Coordinator_Config"].update({
                "Target_Demographic": target } ) # default is Everyone

    cb.add_event(survey_event)
    return

def add_triggered_survey(cb, coverage=1, target='Everyone', start_day=0, diagnostic_type='NewDetectionTech', diagnostic_threshold=40,
                         nodes={"class": "NodeSetAll"}, trigger_string='Diagnostic_Survey', event_name='Diagnostic Survey',
                         positive_diagnosis_config={}) :

    intervention_cfg = {
                    "Diagnostic_Type": diagnostic_type, 
                    "Detection_Threshold": diagnostic_threshold, 
                    "class": "MalariaDiagnostic"                                          
                    }

    if not positive_diagnosis_config :
        intervention_cfg["Event_Or_Config"] = "Event"
        intervention_cfg["Positive_Diagnosis_Event"] = "TestedPositive"    
    else :
        intervention_cfg["Event_Or_Config"] = "Config"
        intervention_cfg["Positive_Diagnosis_Config"] = positive_diagnosis_config   

    survey_event = {   "Event_Name": event_name, 
                        "class": "CampaignEvent",
                        "Start_Day": start_day,
                        "Event_Coordinator_Config": 
                        {
                            "class": "StandardInterventionDistributionEventCoordinator",
                            "Demographic_Coverage": coverage,
                            "Intervention_Config" : { 
                                "class": "NodeLevelHealthTriggeredIV",
                                "Trigger_Condition": "TriggerString",
                                "Trigger_Condition_String": trigger_string,
                                "Actual_IndividualIntervention_Config" : intervention_cfg                                                                        
                            }
                        },
                        "Nodeset_Config": nodes}

    if isinstance(target, dict) and all([k in target.keys() for k in ['agemin','agemax']]) :
        survey_event["Event_Coordinator_Config"].update({
                "Target_Demographic": "ExplicitAgeRanges", 
                "Target_Age_Min": target['agemin'],
                "Target_Age_Max": target['agemax'] })
    else :
        survey_event["Event_Coordinator_Config"].update({
                "Target_Demographic": target } ) # default is Everyone

    cb.add_event(survey_event)
    return