
def recurring_outbreak(cb, outbreak_fraction=0.01, repetitions=-1, tsteps_btwn=365, target='Everyone', start_day=0, strain=(0,0), nodes={"class": "NodeSetAll"}, outbreak_source="PrevalenceIncrease"):
    """
    Function to add recurring introduction of new infections to the current configuration builder

    :param cb: Configuration builder holding the interventions
    :param outbreak_fraction: Fraction of people getting infected by the outbreak
    :param repetitions: Number of repetitions
    :param tsteps_btwn:  Timesteps between repetitions
    :param target: Target demographic. Default is 'Everyone'
    :param start_day: Start day for the outbreak
    :param strain: Needs to be defined as (Antigen,Genome)
    :return: A dictionary holding the fraction and the timesteps between events
    """
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
                                         "Outbreak_Source": outbreak_source, 
                                         "class": "OutbreakIndividual"
                                         }
                                     },
                                 "Nodeset_Config": nodes
                                 }

    cb.add_event(outbreak_event)
    return {'outbreak_fraction': outbreak_fraction,
            'tsteps_btwn': tsteps_btwn}
