def change_biting_risk(cb, start_day=0,
                       risk_config={ 'Risk_Distribution_Type' : 'FIXED_DURATION','Constant' : 1},
                       coverage=1,
                       repetitions=1,
                       tsteps_btwn_repetitions=365,
                       target_group='Everyone',
                       trigger=None,
                       duration=-1,
                       nodeIDs=[],
                       node_property_restrictions=[],
                       ind_property_restrictions=[]
                       ):
    """
    Add an intervention to change individual biting risk as defined by the parameters to the config builder.

    :param cb: The :py:class:`DTKConfigBuilder <dtk.utils.core.DTKConfigBuilder>` that will receive the risk-changing
    intervention.
    :param start_day: date upon which to change biting risk
    :param risk_config: risk distribution type and distribution parameters defining the distribution from which biting
    risk will be drawn. Currently, Risk_Distribution_Type is allowed
        FIXED_DURATION (parameter Constant)
        UNIFORM_DURATION (parameters Uniform_Min, Uniform_Max)
        GAUSSIAN_DURATION (parameters Gaussian_Mean, Gaussian_Std_Dev)
        EXPONENTIAL_DURATION (parameter Exponential_Mean)
    :param coverage: Demographic coverage of the distribution
    :param repetitions: Number of repetitions
    :param tsteps_btwn_repetitions: days between repetitions
    :param target_group: to restrict by age, dict of {'agemin' : x, 'agemax' : y}. Default is targeting everyone.
    :param trigger: for triggered changes, trigger for changing risk. Can be "Birth" or any other trigger string.
    :param duration: for triggered changes, duration after start_day over which triggered risk-changing will happen;
    default is forever
    :param nodeIDs: list of node IDs; if empty, defaults to all nodes
    :param ind_property_restrictions: used with Property_Restrictions_Within_Node. Format: list of dicts:
    [{ "IndividualProperty1" : "PropertyValue1" }, {'IndividualProperty2': "PropertyValue2"}, ...]
    :param node_property_restrictions: used with NodePropertyRestrictions.
    Format: list of dicts: [{ "NodeProperty1" : "PropertyValue1" }, {'NodeProperty2': "PropertyValue2"}, ...]

    I haven't implemented NewPropertyValue or DisqualifyingProperties with this intervention, though they could be
    useful.
    """

    risk_config["class"] = "BitingRisk"

    risk_event = {
        "class": "CampaignEvent",
        "Start_Day": start_day,
        "Nodeset_Config": {
            "class": "NodeSetAll"
        },
        "Event_Coordinator_Config": {
            "class": "StandardInterventionDistributionEventCoordinator",
            "Number_Repetitions": repetitions,
            "Timesteps_Between_Repetitions": tsteps_btwn_repetitions,
            "Target_Demographic": "Everyone",
            "Demographic_Coverage": coverage,
            "Intervention_Config": risk_config
        }
    }

    if target_group != 'Everyone':
        risk_event['Event_Coordinator_Config'].update({
            "Target_Demographic": "ExplicitAgeRanges",  # Otherwise default is Everyone
            "Target_Age_Min": target_group['agemin'],
            "Target_Age_Max": target_group['agemax']
        })

    if not nodeIDs:
        risk_event["Nodeset_Config"] = {"class": "NodeSetAll"}
    else:
        risk_event["Nodeset_Config"] = {"class": "NodeSetNodeList", "Node_List": nodeIDs}

    if node_property_restrictions:
        risk_event['Event_Coordinator_Config']['Node_Property_Restrictions'] =node_property_restrictions

    if ind_property_restrictions:
        risk_event["Event_Coordinator_Config"]["Property_Restrictions_Within_Node"] = ind_property_restrictions

    if trigger :

        if 'birth' in trigger.lower() :
            triggered_intervention = {
                "class": "BirthTriggeredIV",
                "Duration": duration,  # default to forever if  duration not specified
                "Demographic_Coverage": coverage,
                "Actual_IndividualIntervention_Config": risk_config  # itn_bednet
            }

        else :
            triggered_intervention = {
                "class": "NodeLevelHealthTriggeredIV",
                "Demographic_Coverage": coverage,
                "Duration": duration,
                "Trigger_Condition_List": [trigger],
                "Actual_IndividualIntervention_Config" : risk_config
            }

        risk_event["Event_Coordinator_Config"]["Intervention_Config"] = triggered_intervention

        risk_event["Event_Coordinator_Config"].pop("Demographic_Coverage")
        risk_event["Event_Coordinator_Config"].pop("Number_Repetitions")
        risk_event["Event_Coordinator_Config"].pop("Timesteps_Between_Repetitions")
        risk_event["Event_Coordinator_Config"].pop("Target_Demographic")

        if ind_property_restrictions:
            risk_event["Event_Coordinator_Config"].pop("Property_Restrictions_Within_Node")
            risk_event["Event_Coordinator_Config"]["Intervention_Config"]["Property_Restrictions_Within_Node"] = ind_property_restrictions

    cb.add_event(risk_event)