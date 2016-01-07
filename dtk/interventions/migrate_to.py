def add_migration_event(cb, nodeto, start_day=0, coverage=1, repetitions=1, tsteps_btwn=365, 
                        duration_at_node_distr_type='FIXED_DURATION', duration_of_stay=100, 
                        is_family_trip=0, target='Everyone', nodesfrom={"class": "NodeSetAll"}) :

    migration_event = { "Event_Name": "Migration Event", 
                        "class": "CampaignEvent",
                        "Start_Day": start_day, 
                        "Event_Coordinator_Config": {
                            "class": "StandardInterventionDistributionEventCoordinator",
                            "Number_Distributions": -1,
                            "Number_Repetitions": repetitions,
                            "Target_Residents_Only" : 1,
                            "Target_Demographic": "Everyone", 
                            "Timesteps_Between_Repetitions": tsteps_btwn,
                            "Demographic_Coverage": coverage,
                            "Intervention_Config": {
                                "class": "MigrateTo",
                                "NodeID_To_Migrate_To": nodeto,
                                "Is_Family_Trip": is_family_trip,
                                "Is_Moving" : 0 }
                            },
                        "Nodeset_Config": nodesfrom
                        }

    if isinstance(target, dict) and all([k in target.keys() for k in ['agemin','agemax']]) :
        migration_event["Event_Coordinator_Config"].update({
                "Target_Demographic": "ExplicitAgeRanges", 
                "Target_Age_Min": target['agemin'],
                "Target_Age_Max": target['agemax'] })
    else :
        migration_event["Event_Coordinator_Config"].update({
                "Target_Demographic": target } ) # default is Everyone

    if duration_at_node_distr_type == 'FIXED_DURATION' :
        migration_event["Event_Coordinator_Config"]["Intervention_Config"]["Duration_At_Node_Distribution_Type"] = "FIXED_DURATION"
        migration_event["Event_Coordinator_Config"]["Intervention_Config"]["Duration_At_Node_Fixed"] = duration_of_stay
    elif duration_at_node_distr_type == 'UNIFORM_DURATION' :
        migration_event["Event_Coordinator_Config"]["Intervention_Config"]["Duration_At_Node_Distribution_Type"] = "UNIFORM_DURATION"
        migration_event["Event_Coordinator_Config"]["Intervention_Config"]["Duration_At_Node_Uniform_Min"] = duration_of_stay
        migration_event["Event_Coordinator_Config"]["Intervention_Config"]["Duration_At_Node_Uniform_Max"] = duration_of_stay
    elif duration_at_node_distr_type == 'GAUSSIAN_DURATION' :
        migration_event["Event_Coordinator_Config"]["Intervention_Config"]["Duration_At_Node_Distribution_Type"] = "GAUSSIAN_DURATION"
        migration_event["Event_Coordinator_Config"]["Intervention_Config"]["Duration_At_Node_Gausian_Mean"] = duration_of_stay
        migration_event["Event_Coordinator_Config"]["Intervention_Config"]["Duration_At_Node_Gausian_StdDev"] = duration_of_stay
    elif duration_at_node_distr_type == 'EXPONENTIAL_DURATION' :
        migration_event["Event_Coordinator_Config"]["Intervention_Config"]["Duration_At_Node_Distribution_Type"] = "EXPONENTIAL_DURATION"
        migration_event["Event_Coordinator_Config"]["Intervention_Config"]["Duration_At_Node_Exponential_Period"] = duration_of_stay
    elif duration_at_node_distr_type == 'POISSON_DURATION' :
        migration_event["Event_Coordinator_Config"]["Intervention_Config"]["Duration_At_Node_Distribution_Type"] = "POISSON_DURATION"
        migration_event["Event_Coordinator_Config"]["Intervention_Config"]["Duration_At_Node_Poisson_Mean"] = duration_of_stay
    else :
        print "warning: unsupported duration distribution type, reverting to fixed duration"
        migration_event["Event_Coordinator_Config"]["Intervention_Config"]["Duration_At_Node_Distribution_Type"] = "FIXED_DURATION"
        migration_event["Event_Coordinator_Config"]["Intervention_Config"]["Duration_At_Node_Fixed"] = duration_of_stay

    cb.add_event(migration_event)
