from dtk.interventions.malaria_drugs import drug_configs_from_code
from dtk.interventions.malaria_diagnostic import add_diagnostic_survey, add_triggered_survey
from copy import deepcopy

def add_drug_campaign(cb, drug_code, start_days, coverage=1.0, repetitions=3, interval=60, diagnostic_threshold=40, node_selection_type='DISTANCE_ONLY',
                      trigger_coverage=1.0, snowballs=0, delay=0, nodes={"class": "NodeSetAll"}, target_group='Everyone'):
    """
    Add a drug campaign defined by the parameters to the config builder.

    :param cb: The :py:class:`DTKConfigBuilder <dtk.utils.core.DTKConfigBuilder>` that will receive the drug intervention.
    :param drug_code: The drug code of the drug regimen
    :param start_days: List of start days where the drug regimen will be distributed
    :param coverage: Demographic coverage of the distribution
    :param trigger_coverage: for RCD, fraction of trigger events that will trigger an RCD. coverage param sets the fraction of individuals reached during RCD response.
    :param repetitions: Number repetitions
    :param interval: Timesteps between the repetitions
    :return: Nothing

    Accepted campaign codes:
    MDA
    MSAT
    fMDA
    rfMSAT
    rfMDA
    """
    campaign_type = drug_code.split('_')[0]
    drugs = drug_code.split('_')[-1]
    drug_configs = drug_configs_from_code(cb,'MDA_' + drugs)

    receiving_drugs_event = {
            "class": "BroadcastEvent",
            "Broadcast_Event": "Received_Campaign_Drugs"
            }
    if 'Vehicle' in drug_code :
        receiving_drugs_event["Broadcast_Event"] = "Received_Vehicle"

    if campaign_type not in ['MDA', 'MSAT'] :
        fmda_setup = fmda_cfg(drug_code.split('_')[1], node_selection_type)
        snowball_setup = [deepcopy(fmda_setup) for x in range(snowballs+1)]
        for snowball in range(snowballs+1) :
            snowball_setup[snowball]['Event_Trigger'] = 'Diagnostic_Survey_' + str(snowball)

    if campaign_type == 'MDA' : # standard drug campaign: MDA, no event triggering

        for start_day in start_days:
            drug_event = {
                "class": "CampaignEvent",
                "Start_Day": start_day,
                "Event_Coordinator_Config": {
                    "class": "MultiInterventionEventCoordinator",
                    "Target_Demographic": "Everyone",
                    "Demographic_Coverage": coverage,
                    "Intervention_Configs": drug_configs + [receiving_drugs_event],
                    "Number_Repetitions": repetitions,
                    "Timesteps_Between_Repetitions": interval
                    }, 
                "Nodeset_Config": nodes
                }

            cb.add_event(drug_event)

    elif campaign_type == 'MSAT' : # standard drug campaign: MSAT, no event triggering

        # MSAT controlled by MalariaDiagnostic campaign event rather than New_Diagnostic_Sensitivity
        for start_day in start_days:
            add_diagnostic_survey(cb, coverage=coverage, repetitions=repetitions, tsteps_btwn=interval, target=target_group, start_day=start_day, 
                                    diagnostic_type='Other', diagnostic_threshold=diagnostic_threshold,
                                    nodes=nodes, positive_diagnosis_configs= drug_configs + [receiving_drugs_event] )

    elif campaign_type == 'rfMSAT' :

        rcd_event = {   "Event_Name": "Trigger RCD MSAT", 
                        "class": "CampaignEvent",
                        "Start_Day": start_days[0],
                        "Event_Coordinator_Config": 
                        {
                            "class": "StandardInterventionDistributionEventCoordinator",
                            "Intervention_Config" : { 
                                "class": "NodeLevelHealthTriggeredIV",
                                "Demographic_Coverage": trigger_coverage,
                                "Trigger_Condition": "TriggerString",
                                "Trigger_Condition_String": "Received_Treatment", # triggered by successful health-seeking
                                "Duration" : interval, # interval argument indicates how long RCD will be implemented
                                "Actual_IndividualIntervention_Config" : { 
                                    "class": "DelayedIntervention",                    
                                    "Delay_Distribution": "FIXED_DURATION",
                                    "Delay_Period": delay,
                                    "Actual_IndividualIntervention_Configs" : [snowball_setup[0]]
                                    }
                            }
                        },
                        "Nodeset_Config": nodes}
        add_triggered_survey(cb, coverage=coverage, start_day=start_days[0], 
                                diagnostic_type='Other', diagnostic_threshold=diagnostic_threshold, nodes=nodes, 
                                trigger_string=snowball_setup[0]['Event_Trigger'], event_name='Reactive MSAT level 0', 
                                positive_diagnosis_configs=drug_configs + [receiving_drugs_event])
        cb.add_event(rcd_event)
        for snowball in range(snowballs) :
            curr_trigger = snowball_setup[snowball]['Event_Trigger']
            add_triggered_survey(cb, coverage=coverage, start_day=start_days[0], 
                                    diagnostic_type='Other', diagnostic_threshold=diagnostic_threshold, nodes=nodes, 
                                    trigger_string=curr_trigger, event_name='Snowball level ' + str(snowball), 
                                    positive_diagnosis_configs=[snowball_setup[snowball+1], receiving_drugs_event]+drug_configs)

    elif campaign_type in ['fMDA', 'rfMDA'] :

        if campaign_type == 'fMDA' :
            for start_day in start_days :
                add_diagnostic_survey(cb, coverage=coverage, repetitions=repetitions, tsteps_btwn=interval, target=target_group, start_day=start_day, 
                                      diagnostic_type='Other', diagnostic_threshold=diagnostic_threshold,
                                      nodes=nodes, positive_diagnosis_configs=[fmda_setup] )

        elif campaign_type == 'rfMDA' :
            rcd_event = {   "Event_Name": "Trigger RCD MDA", 
                            "class": "CampaignEvent",
                            "Start_Day": start_days[0],
                            "Event_Coordinator_Config": 
                            {
                                "class": "StandardInterventionDistributionEventCoordinator",
                                "Intervention_Config" : { 
                                    "class": "NodeLevelHealthTriggeredIV",
                                    "Demographic_Coverage": trigger_coverage,
                                    "Trigger_Condition": "TriggerString",
                                    "Trigger_Condition_String": "Received_Treatment", # triggered by successful health-seeking
                                    "Duration" : interval, # interval argument indicates how long RCD will be implemented
                                    "Actual_IndividualIntervention_Config" : { 
                                        "class": "DelayedIntervention",                    
                                        "Delay_Distribution": "FIXED_DURATION",
                                        "Delay_Period": delay,
                                        "Actual_IndividualIntervention_Configs" : [snowball_setup[0], fmda_setup]
                                        }
                                }
                            },
                            "Nodeset_Config": nodes}
            cb.add_event(rcd_event)

            for snowball in range(snowballs) :
                curr_trigger = snowball_setup[snowball]['Event_Trigger']
                add_triggered_survey(cb, coverage=coverage, start_day=start_days[0], 
                                     diagnostic_type='Other', diagnostic_threshold=diagnostic_threshold, nodes=nodes, 
                                     trigger_string=curr_trigger, event_name='Snowball level ' + str(snowball), 
                                     positive_diagnosis_configs=[snowball_setup[snowball+1], fmda_setup])

        # distributes drugs to individuals broadcasting "Give_Drugs"
        # who is broadcasting is determined by other events
        # if campaign drugs change (less effective, different cocktail), then this event should have an expiration date.
        fmda_distribute_drugs = {   "Event_Name": "Distribute fMDA", 
                                    "class": "CampaignEvent",
                                    "Start_Day": start_days[0],
                                    "Event_Coordinator_Config": 
                                    {
                                        "class": "StandardInterventionDistributionEventCoordinator",
                                        "Intervention_Config" : { 
                                            "class": "NodeLevelHealthTriggeredIV",
                                            "Demographic_Coverage": 1.0, # coverage is set in diagnostic_survey, rcd_event, and triggered_survey
                                            "Trigger_Condition": "TriggerString",
                                            "Trigger_Condition_String": "Give_Drugs",
                                            "Blackout_Event_Trigger" : "Blackout",
                                            "Blackout_Period" : 3.0,
                                            "Actual_IndividualIntervention_Config" : {
                                                "Intervention_List" : drug_configs + [receiving_drugs_event] ,
                                                "class" : "MultiInterventionDistributor"
                                            }                                            
                                        }
                                    },
                                    "Nodeset_Config": {"class": "NodeSetAll"}
                                }

        cb.add_event(fmda_distribute_drugs)

    else :
        return
    """ think more about how to set this up
    elif campaign_type in ['borderscreen'] :
        drug_configs = drug_configs_from_code(cb,'MDA_' + drugs)
        add_triggered_survey(cb, coverage=coverage, start_day=start_days[0], 
                            diagnostic_type='Other', diagnostic_threshold=diagnostic_threshold, nodes=nodes, 
                            trigger_string='Emigrating', event_name='Border screening', 
                            positive_diagnosis_config={ "class": "BroadcastEvent",
                                                        "Broadcast_Event": "Give_Drugs" } )
    """
        
def fmda_cfg(fmda_type, node_selection_type) :

    # defaults to household-only unless fmda_type is a distance in km
    # options on Node_Selection_Type :
    # DISTANCE_ONLY: It will send the event to nodes that are within a given distance.
    # MIGRATION_NODES_ONLY: It will only send the event to nodes that the individual can migrate to.
    # DISTANCE_AND_MIGRATION: It will only send the even to migratable nodes that are within a given distance. Migrateable nodes = Local and Regional.

    fmda = {
            "class": "BroadcastEventToOtherNodes",
            "Event_Trigger": "Give_Drugs",
            "Include_My_Node" : 1,
            "Node_Selection_Type" : node_selection_type,
            "Max_Distance_To_Other_Nodes_Km" : 0                                        
            }
    try :
        fmda["Max_Distance_To_Other_Nodes_Km"] = float(fmda_type)
    except ValueError :
        pass
    return fmda

"""
    treatment_ineligibility_event = {
            "Description": "One week treatment ineligibility",
            "class": "CampaignEvent",
            "Start_Day": 0,
            "Nodeset_Config": { "class": "NodeSetAll" },
            "Event_Coordinator_Config": 
            {
            "class": "StandardInterventionDistributionEventCoordinator",
            "Demographic_Coverage": 1,
            "Intervention_Config": {
                "class": "NodeLevelHealthTriggeredIV",
	            "Trigger_Condition": "TriggerList",
                "Trigger_Condition_List": [
                    "Received_Treatment",
                    "Received_Campaign_Drugs"
                ],
	            "Actual_IndividualIntervention_Config": 
                    {
                        "class": "HIVDelayedIntervention",
	                    "Abort_States": [ "Abort_Ineligibility" ],
	                    "Cascade_State": "Ineligible_For_Drugs",
	                    "Delay_Distribution": "FIXED_DURATION",
	                    "Delay_Period": 7,
                        "Broadcast_Event": "Done_Waiting"
                    }
                }
            }
        }
    end_ineligibility_event = {
           "Description": "End treatment ineligibility",
           "class": "CampaignEvent",
           "Start_Day": 0,
           "Nodeset_Config": { "class": "NodeSetAll" },
           "Event_Coordinator_Config": 
           {
              "class": "StandardInterventionDistributionEventCoordinator",
              "Demographic_Coverage": 1,
              "Intervention_Config": 
              {
                 "class": "NodeLevelHealthTriggeredIV",
                 "Trigger_Condition": "TriggerString",
                 "Trigger_Condition_String": "Done_Waiting",
                 "Actual_IndividualIntervention_Config": 
                 {
                    "class": "HIVSetCascadeState",
                    "Abort_States": [ ],
                    "Cascade_State": "Abort_Ineligibility"
                 }
              }
           }
        }
    cb.add_event(treatment_ineligibility_event)
    cb.add_event(end_ineligibility_event)
"""
