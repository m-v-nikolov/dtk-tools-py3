def setup_recent_drug_states(cb, drug_events=["Received_Treatment", "Received_Campaign_Drugs", "Received_RCD_Drugs"],
                             ineligible_window=14) :

    cb.update_params( { "Valid_Intervention_States" : ["None", "Recent_Drug"]})

    set_to_recent_drugs = {"class": "SetInterventionState",
                           "Invalid_Intervention_States": [],
                           "Intervention_State": "Recent_Drug"
                           }


    expire_recent_drugs = {"class": "DelayedIntervention",
                           "Delay_Distribution": "FIXED_DURATION",
                           "Delay_Period": ineligible_window,
                           "Actual_IndividualIntervention_Configs":
                               [{"class": "SetInterventionState",
                                 "Invalid_Intervention_States": [],
                                 "Intervention_State": "None"
                                 }]
                           }

    set_treatment_states = { "Event_Name": "InterventionState Set Drug State after Treatment",
                             "class": "CampaignEvent",
                             "Start_Day": 1,
                             "Event_Coordinator_Config":
                                 {
                                     "class": "StandardInterventionDistributionEventCoordinator",
                                     "Intervention_Config": {
                                         "class": "NodeLevelHealthTriggeredIV",
                                         "Trigger_Condition_List": [drug_events],
                                         "Actual_IndividualIntervention_Config": {
                                             "class": "MultiInterventionDistributor",
                                                      "Intervention_List" : [set_to_recent_drugs, expire_recent_drugs] }
                                     }
                                 },
                             "Nodeset_Config": {"class": "NodeSetAll"}}

    return set_treatment_states


def update_intervention_state_start_day(cb, start_day) :

    for event in cb.campaign['Events'] :
        try :
            if event['Event_Name'].split()[0] == 'InterventionState' :
                event['Start_Day'] = start_day
        except KeyError :
            pass