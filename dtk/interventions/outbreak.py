# Recurring introduction of new infections
def recurring_outbreak(campaign, outbreak_fraction=0.01, repetitions=-1, tsteps_btwn=365, target='Everyone', start_day=0, strain=(0,0)):

    outbreak_event = { "class" : "CampaignEvent",
                                 "Start_Day": start_day,
                                 "Event_Coordinator_Config": {
                                     "class": "StandardInterventionDistributionEventCoordinator",
                                     "Number_Distributions": -1,
                                     "Number_Repetitions": repetitions,
                                     "Timesteps_Between_Repetitions": tsteps_btwn,
                                     "Target_Demographic": target,
                                     "Demographic_Coverage": outbreak_fraction,
                                     "Intervention_Config": {
                                         "Antigen": strain[0], 
                                         "Genome": strain[1], 
                                         "Outbreak_Source": "PrevalenceIncrease", 
                                         "class": "OutbreakIndividual"
                                         }
                                     },
                                 "Nodeset_Config": {
                                     "class": "NodeSetAll"
                                     }
                                 }
    campaign["Events"].append(outbreak_event)

    return campaign
