
def add_ATSB(config_builder, start, initial_killing=0.15, duration=180, cost=None, nodeIDs=[]):

    atsb_config = { 
                    "Cost_To_Consumer": cost, 
                    "Killing_Config": {
                        "Decay_Time_Constant": duration, 
                        "Initial_Effect": initial_killing, 
                        "class": "WaningEffectBox"
                    }, 
                    "class": "SugarTrap"
                }

    ATSB_event = {   "Event_Coordinator_Config": {
                        "Intervention_Config": atsb_config, 
                        "class": "NodeEventCoordinator"
                    }, 
                    "Nodeset_Config": {
                        "class": "NodeSetAll"
                    }, 
                    "Start_Day": start, 
                    "Event_Name": "Attractive Toxic Sugar Bait",
                    "class": "CampaignEvent"
                }

    if nodeIDs:
        ATSB_event["Nodeset_Config"] = { "class": "NodeSetNodeList", "Node_List": nodeIDs }

    config_builder.add_event(ATSB_event)


def add_topical_repellent(config_builder, start, coverage_by_ages, cost=None, initial_blocking=0.95, duration=0.3, 
                          repetitions=1, interval=1, nodeIDs=[]):

    repellent = {   "class": "SimpleIndividualRepellent",
                    "Event_Name": "Individual Repellent",
                    "Blocking_Config": {
                        "Initial_Effect": initial_blocking,
                        "Decay_Time_Constant": duration,
                        "class": "WaningEffectBox"
                    },
                   "Cost_To_Consumer": cost
    }

    for coverage_by_age in coverage_by_ages:

        repellent_event = { "class" : "CampaignEvent",
                          "Start_Day": start,
                          "Event_Coordinator_Config": {
                              "class": "StandardInterventionDistributionEventCoordinator",
                              "Target_Residents_Only" : 0,
                              "Demographic_Coverage": coverage_by_age["coverage"],
                              "Intervention_Config": repellent,
                              "Number_Repetitions": repetitions,
                              "Timesteps_Between_Repetitions": interval
                          }
                        }

        if all([k in coverage_by_age.keys() for k in ['min','max']]):
            repellent_event["Event_Coordinator_Config"].update({
                   "Target_Demographic": "ExplicitAgeRanges",
                   "Target_Age_Min": coverage_by_age["min"],
                   "Target_Age_Max": coverage_by_age["max"]})

        if not nodeIDs:
            repellent_event["Nodeset_Config"] = { "class": "NodeSetAll" }
        else:
            repellent_event["Nodeset_Config"] = { "class": "NodeSetNodeList", "Node_List": nodeIDs }

        if 'birth' in coverage_by_age.keys() and coverage_by_age['birth']:
            birth_triggered_intervention = {
                "class": "BirthTriggeredIV",
                "Duration": coverage_by_age.get('duration', -1), # default to forever if  duration not specified
                "Demographic_Coverage": coverage_by_age["coverage"],
                "Actual_IndividualIntervention_Config": itn_bednet_w_event #itn_bednet
            }

            repellent_event["Event_Coordinator_Config"]["Intervention_Config"] = birth_triggered_intervention
            repellent_event["Event_Coordinator_Config"].pop("Demographic_Coverage")
            repellent_event["Event_Coordinator_Config"].pop("Target_Residents_Only")

        config_builder.add_event(repellent_event)



def add_ors_node(config_builder, start, coverage=1, initial_killing=0.95, duration=180, cost=None, 
                 repetitions=1, interval=1, nodeIDs=[]):

    ors_config = {  "Reduction_Config": {
                        "Decay_Time_Constant": 365, 
                        "Initial_Effect": 0, 
                        "class": "WaningEffectBox"
                    }, 
                    "Habitat_Target": "ALL_HABITATS", 
                    "Cost_To_Consumer": cost, 
                    "Killing_Config": {
                        "Decay_Time_Constant": duration, 
                        "Initial_Effect": initial_killing*coverage, 
                        "class": "WaningEffectBox"
                    }, 
                    "Spray_Kill_Target": "SpaceSpray_FemalesAndMales", 
                    "class": "SpaceSpraying"
                }

    ORS_event = {   "Event_Coordinator_Config": {
                        "Intervention_Config": ors_config, 
                        "Number_Repetitions": repetitions,
                        "Timesteps_Between_Repetitions": interval,
                        "class": "NodeEventCoordinator"
                    }, 
                    "Nodeset_Config": {
                        "class": "NodeSetAll"
                    }, 
                    "Start_Day": start, 
                    "Event_Name": "Outdoor Residual Spray",
                    "class": "CampaignEvent"
                }

    if nodeIDs:
        ORS_event["Nodeset_Config"] = { "class": "NodeSetNodeList", "Node_List": nodeIDs }

    config_builder.add_event(ORS_event)


def add_larvicide(config_builder, start, coverage=1, initial_killing=1.0, duration=30, cost=None, 
                  habitat_target="ALL_HABITATS", repetitions=1, interval=1, nodeIDs=[]):

    larvicide_config = {  "Reduction_Config": {
                        "Decay_Time_Constant": 365, 
                        "Initial_Effect": 0, 
                        "class": "WaningEffectBox"
                    }, 
                    "Habitat_Target": habitat_target, 
                    "Cost_To_Consumer": cost, 
                    "Killing_Config": {
                        "Decay_Time_Constant": duration, 
                        "Initial_Effect": initial_killing*coverage, 
                        "class": "WaningEffectBox"
                    }, 
                    "class": "Larvicides"
                }

    larvicide_event = {   "Event_Coordinator_Config": {
                        "Intervention_Config": larvicide_config, 
                        "Number_Repetitions": repetitions,
                        "Timesteps_Between_Repetitions": interval,
                        "class": "NodeEventCoordinator"
                    }, 
                    "Nodeset_Config": {
                        "class": "NodeSetAll"
                    }, 
                    "Start_Day": start, 
                    "Event_Name": "Larvicide",
                    "class": "CampaignEvent"
                }

    if nodeIDs:
        larvicide_event["Nodeset_Config"] = { "class": "NodeSetNodeList", "Node_List": nodeIDs }

    config_builder.add_event(larvicide_event)


def add_eave_tubes(config_builder, start, coverage=1, initial_killing=1.0, killing_duration=180, 
                   initial_blocking=0.8, blocking_duration=730, outdoor_killing_discount=0.3, cost=None, 
                   habitat_target="ALL_HABITATS", repetitions=1, interval=1, nodeIDs=[]):

    indoor_config = {   "class": "IRSHousingModification",
                        "Killing_Config": {
                            "Decay_Time_Constant": duration, 
                            "Initial_Effect": initial_killing, 
                            "class": "WaningEffectBox"
                        },
                        "Blocking_Config": {
                            "Decay_Time_Constant": blocking_duration, 
                            "Initial_Effect": initial_blocking, 
                            "class": "WaningEffectBox"
                        },
                        "Cost_To_Consumer": cost
                        }

    indoor_event = {"class": "CampaignEvent",
                    "Start_Day": start,
                    "Event_Coordinator_Config": {
                        "class": "StandardInterventionDistributionEventCoordinator",
                        "Demographic_Coverage": coverage,
                        "Target_Demographic": "Everyone",
                        "Intervention_Config": indoor_config
                    }
                    }

    if nodeIDs:
        indoor_event["Nodeset_Config"] = { "class": "NodeSetNodeList", "Node_List": nodeIDs }

    config_builder.add_event(indoor_event)
    add_ors_node(config_builder, start, coverage=coverage, 
                 initial_killing=initial_killing*outdoor_killing_discount, 
                 duration=killing_duration, cost=cost, 
                 repetitions=repetitions, interval=interval, nodeIDs=nodeIDs)