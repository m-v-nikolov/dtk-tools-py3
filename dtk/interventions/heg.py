def heg_release(cb):
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
                     "Released_Number": 500, 
                     "Released_Species": "arabiensis", 
                     "Cost_To_Consumer": 200,
                     "Cost_To_Consumer_Citation" : "Alphey et al Vector Borne Zoonotic Dis 2010 10 295 by projecting 1979 An albimanus cost in El Salvador to 2008 dollars",
                     "class": "MosquitoRelease"
                }, 
                "Number_Repetitions": 52, 
                "Timesteps_Between_Repetitions": 7,
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