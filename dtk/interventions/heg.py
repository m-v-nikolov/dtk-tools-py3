def heg_release(cb, released_number, num_repetitions = 13, timesteps_between_reps = 14):
    """
    Homing endonucleouse genetic intervention.

    :param cb: The :py:class:`DTKConfigBuilder <dtk.utils.core.DTKConfigBuilder>` object
    :return: Nothing
    """

    
    heg_release_event = {
           "Event_Coordinator_Config": {
                "Intervention_Config": {
                     "Released_Gender": "VECTOR_MALE",
                     "Released_Sterility": "VECTOR_FERTILE",
                     "Released_Genetics": {
                         "Pesticide_Resistance": "WILD",
                         "HEG": "FULL"
                     },
                     "Mated_Genetics": {
                         "Pesticide_Resistance": "NotMated",
                         "HEG": "NotMated"
                     },
                     "Released_HEGs": ["FULL", "NotMated"],
                     "Released_Number": released_number, 
                     "Released_Species": "arabiensis", 
                     "Cost_To_Consumer": 200,
                     "Cost_To_Consumer_Citation" : "Alphey et al Vector Borne Zoonotic Dis 2010 10 295 by projecting 1979 An albimanus cost in El Salvador to 2008 dollars",
                     "class": "MosquitoRelease"
                }, 
                "Number_Repetitions": num_repetitions, 
                "Timesteps_Between_Repetitions": timesteps_between_reps,
                "class": "StandardInterventionDistributionEventCoordinator"
           }, 
           "Event_Name": "MosquitoRelease", 
           "Nodeset_Config": {
                "class": "NodeSetNodeList",
                    "Node_List": [340461476]
           }, 
           "Start_Day": 365, 
           "class": "CampaignEvent"
      }

    cb.add_event(heg_release_event)
    
    return {'num_released':released_number,
            'num_repetitions':num_repetitions,
            'timesteps_btw_reps':timesteps_between_reps}