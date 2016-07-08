import copy

default_larvicides = {
    "Blocking_Config": {
        "Box_Duration": 100,
        "Decay_Time_Constant": 150,
        "Initial_Effect": 0.4,
        "class": "WaningEffectBoxExponential"
    },
    "Cost_To_Consumer": 1.0,
    "Habitat_Target": "ALL_HABITATS",
    "Killing_Config": {
        "Box_Duration": 100,
        "Decay_Time_Constant": 150,
        "Initial_Effect": 0.2,
        "class": "WaningEffectBoxExponential"
    },
    "class": "Larvicides"
}


def add_larvicides(config_builder, start, killing=None, reduction=None, habitat_target=None, waning=None, nodesIDs = None):
    # Create our event dictionary
    event = {
        "Start_Day": start,
        "class": "CampaignEvent",
        "Event_Coordinator_Config":{
            "class": "StandardInterventionDistributionEventCoordinator"
        }
    }

    # Take care of specified NodeIDs if any
    if not nodesIDs:
        event['Nodeset_Config'] = {"class": "NodeSetAll"}
    else:
        event["Nodeset_Config"] = {"class": "NodeSetNodeList", "Node_List": nodesIDs}

    # Copy the default event
    larvicides_event = copy.deepcopy(default_larvicides)

    # Change according to parameters
    if killing:
        larvicides_event["Killing_Config"]["Initial_Effect"] = killing

    if reduction:
        larvicides_event["Blocking_Config"]["Initial_Effect"] = reduction

    if habitat_target:
        larvicides_event["Habitat_Target"] = habitat_target

    if waning:
        if "blocking" in waning:
            larvicides_event["Blocking_Config"].update(waning["blocking"])
        if "killing" in waning:
            larvicides_event["Killing_Config"].update(waning["killing"])

    # Add the larvicides to the event coordinator
    event["Event_Coordinator_Config"]["Intervention_Config"] = larvicides_event\

    # Add to the config builder
    config_builder.add_event(event)
