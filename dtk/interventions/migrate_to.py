def add_migration_event(cb, nodeto, start_day=0, coverage=1, repetitions=1, tsteps_btwn=365, duration_of_stay=100, is_family_trip=0, target='Everyone', nodesfrom={"class": "NodeSetAll"}) :

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
                                "Duration_At_Node": duration_of_stay, 
                                "Is_Family_Trip": is_family_trip }
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

    cb.add_event(migration_event)