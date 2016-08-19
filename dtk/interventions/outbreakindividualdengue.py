# Add dengue outbreak individual event
def add_OutbreakIndivisualDengue(config_builder, start, coverage_by_age, strain_id_name, nodeIDs=[]):
    dengue_event = {
        "class": "CampaignEvent",
        "Start_Day": int(start),
        "Event_Coordinator_Config": {
            "class": "StandardInterventionDistributionEventCoordinator",
            "Intervention_Config": {
                "Strain_Id_Name": strain_id_name,  # eg. "Strain_1"
                "class": "OutbreakIndividualDengue"
            }
        }
    }

    if all([k in coverage_by_age.keys() for k in ['min', 'max']]):
        dengue_event["Event_Coordinator_Config"].update({
            "Target_Demographic": "ExplicitAgeRanges",
            "Target_Age_Min": coverage_by_age["min"],
            "Target_Age_Max": coverage_by_age["max"]})

    # not sure else is the correct way to do eg.{min: 0} or {max: 1.725}
    else:
        dengue_event["Event_Coordinator_Config"].update({
            "Demographic_Coverage": 0,
            "Target_Demographic": "Everyone"})

    if not nodeIDs:
        dengue_event["Nodeset_Config"] = {"class": "NodeSetAll"}
    else:
        dengue_event["Nodeset_Config"] = {"class": "NodeSetNodeList", "Node_List": nodeIDs}

    config_builder.add_event(dengue_event)
