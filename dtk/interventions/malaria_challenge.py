def add_challenge_trial(config_builder):
    """
    Add a MalariaChallenge to the passed config_builder with default parameters.

    :param config_builder: The :py:class:`DTKConfigBuilder <dtk.utils.core.DTKConfigBuilder>` that will receive the intervention.
    :return: Nothing
    """
    # No mosquitoes or births/deaths
    config_builder.update_params({"Vector_Species_Names" : [],
                                  "Enable_Vital_Dynamics" : 0})

    # Infectious-bite challenge
    challenge_event = {
        "class": "CampaignEvent", 
        "Start_Day": 0, 
        "Event_Coordinator_Config": {
            "class": "StandardInterventionDistributionEventCoordinator", 
            "Number_Distributions": -1,
            "Number_Repetitions": 1,
            "Timesteps_Between_Repetitions": 1,
             "Intervention_Config": {
                "class": "MalariaChallenge",
                "Challenge_Type": "InfectiousBites", 
                "Infectious_Bite_Count": 5
             }
         }, 
         "Nodeset_Config": {
             "class": "NodeSetAll"
         }
     }

    config_builder.add_event(challenge_event)
