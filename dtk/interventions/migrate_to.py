# the old MigrateTo has now been split into MigrateIndividuals and MigrateFamily.
# add_migration_event adds a MigrateIndividuals event.
def add_migration_event(cb, nodeto, start_day=0, coverage=1, repetitions=1, tsteps_btwn=365,
                        duration_at_node_distr_type='FIXED_DURATION', 
                        duration_of_stay=100, duration_of_stay_2=0, 
                        duration_before_leaving_distr_type='FIXED_DURATION', 
                        duration_before_leaving=0, duration_before_leaving_2=0, 
                        target='Everyone', nodesfrom={"class": "NodeSetAll"},
                        ind_property_restrictions=[]) :

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
                                "class": "MigrateIndividuals",
                                "NodeID_To_Migrate_To": nodeto,
                                "Is_Moving" : 0 }
                            },
                        "Nodeset_Config": nodesfrom
                        }

    migration_event = update_duration_type(migration_event, duration_at_node_distr_type, 
                                           dur_param_1=duration_of_stay, dur_param_2=duration_of_stay_2, 
                                           leaving_or_at='at')
    migration_event = update_duration_type(migration_event, duration_before_leaving_distr_type, 
                                           dur_param_1=duration_before_leaving, dur_param_2=duration_before_leaving_2, 
                                           leaving_or_at='leaving')

    if isinstance(target, dict) and all([k in target.keys() for k in ['agemin','agemax']]) :
        migration_event["Event_Coordinator_Config"].update({
                "Target_Demographic": "ExplicitAgeRanges", 
                "Target_Age_Min": target['agemin'],
                "Target_Age_Max": target['agemax'] })
    else :
        migration_event["Event_Coordinator_Config"].update({
                "Target_Demographic": target } ) # default is Everyone

    # Add IP restriction on who gets to travel
    if ind_property_restrictions:
        migration_event["Event_Coordinator_Config"]["Property_Restrictions_Within_Node"] = ind_property_restrictions

    cb.add_event(migration_event)

def update_duration_type(migration_event, duration_at_node_distr_type, dur_param_1=0, dur_param_2=0, leaving_or_at='at') :

    if leaving_or_at == 'leaving' :
        trip_end = 'Before_Leaving'
    else :
        trip_end = 'At_Node'

    if duration_at_node_distr_type == 'FIXED_DURATION' :
        migration_event["Event_Coordinator_Config"]["Intervention_Config"]["Duration_" + trip_end + "_Distribution_Type"] = "FIXED_DURATION"
        migration_event["Event_Coordinator_Config"]["Intervention_Config"]["Duration_" + trip_end + "_Fixed"] = dur_param_1
    elif duration_at_node_distr_type == 'UNIFORM_DURATION' :
        migration_event["Event_Coordinator_Config"]["Intervention_Config"]["Duration_" + trip_end + "_Distribution_Type"] = "UNIFORM_DURATION"
        migration_event["Event_Coordinator_Config"]["Intervention_Config"]["Duration_" + trip_end + "_Uniform_Min"] = dur_param_1
        migration_event["Event_Coordinator_Config"]["Intervention_Config"]["Duration_" + trip_end + "_Uniform_Max"] = dur_param_2
    elif duration_at_node_distr_type == 'GAUSSIAN_DURATION' :
        migration_event["Event_Coordinator_Config"]["Intervention_Config"]["Duration_" + trip_end + "_Distribution_Type"] = "GAUSSIAN_DURATION"
        migration_event["Event_Coordinator_Config"]["Intervention_Config"]["Duration_" + trip_end + "_Gausian_Mean"] = dur_param_1
        migration_event["Event_Coordinator_Config"]["Intervention_Config"]["Duration_" + trip_end + "_Gausian_StdDev"] = dur_param_2
    elif duration_at_node_distr_type == 'EXPONENTIAL_DURATION' :
        migration_event["Event_Coordinator_Config"]["Intervention_Config"]["Duration_" + trip_end + "_Distribution_Type"] = "EXPONENTIAL_DURATION"
        migration_event["Event_Coordinator_Config"]["Intervention_Config"]["Duration_" + trip_end + "_Exponential_Period"] = dur_param_1
    elif duration_at_node_distr_type == 'POISSON_DURATION' :
        migration_event["Event_Coordinator_Config"]["Intervention_Config"]["Duration_" + trip_end + "_Distribution_Type"] = "POISSON_DURATION"
        migration_event["Event_Coordinator_Config"]["Intervention_Config"]["Duration_" + trip_end + "_Poisson_Mean"] = dur_param_1
    else :
        print("warning: unsupported duration distribution type, reverting to fixed duration")
        migration_event["Event_Coordinator_Config"]["Intervention_Config"]["Duration_" + trip_end + "_Distribution_Type"] = "FIXED_DURATION"
        migration_event["Event_Coordinator_Config"]["Intervention_Config"]["Duration_" + trip_end + "_Fixed"] = dur_param_1

    return migration_event