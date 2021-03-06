
def add_mosquito_release(cb, start_day, species, number=100, repetitions=-1, tsteps_btwn=365, gender='VECTOR_FEMALE', sterility='VECTOR_FERTILE',
                         released_genetics={ "Pesticide_Resistance" : "WILD", "HEG" : "WILD" }, 
                         mated_genetics={ "Pesticide_Resistance" : "WILD", "HEG" : "WILD" }, 
                         nodes={"class": "NodeSetAll"}):
    """
    Function to add recurring introduction of new new vectors

    :param cb: Configuration builder holding the interventions
    :param repetitions: Number of repetitions
    :param tsteps_btwn:  Timesteps between repetitions
    :param start_day: Start day for the first release
    """
    release_event = { "class" : "CampaignEvent",
                      "Event_Name" : "Mosquito Release",
                        "Start_Day": start_day,
                        "Event_Coordinator_Config": {
                            "class": "StandardInterventionDistributionEventCoordinator",
                            "Number_Distributions": -1,
                            "Number_Repetitions": repetitions,
                            "Timesteps_Between_Repetitions": tsteps_btwn,
                            "Target_Demographic": "Everyone",
                            "Intervention_Config": {        
                                    "Released_Number": number, 
                                    "Released_Species": species, 
                                    "Released_Gender": gender, 
                                    "Released_Sterility": sterility, 
                                    "Released_Genetics": {
                                        "Pesticide_Resistance" : released_genetics['Pesticide_Resistance'],
                                        "HEG" : released_genetics['HEG']
                                        }, 
                                    "Mated_Genetics": {
                                        "Pesticide_Resistance" : mated_genetics['Pesticide_Resistance'],
                                        "HEG" : mated_genetics['HEG']
                                        }, 
                                    "class": "MosquitoRelease"
                                } 
                            },
                        "Nodeset_Config": nodes
                        }

    cb.add_event(release_event)
