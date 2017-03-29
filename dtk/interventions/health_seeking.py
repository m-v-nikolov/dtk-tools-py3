receiving_drugs_event = {
    "class": "BroadcastEvent",
    "Broadcast_Event": "Received_Treatment"
}
expire_recent_drugs = {"class": "PropertyValueChanger",
                       "Target_Property_Key": "DrugStatus",
                       "Target_Property_Value": "RecentDrug",
                       "Daily_Probability": 1.0,
                       "Maximum_Duration": 0,
                       'Revert': 0
                       }


def add_health_seeking(config_builder,
                       start_day=0,
                       # Note: potential for overlapping drug treatments in the same individual
                       targets=[{'trigger': 'NewClinicalCase', 'coverage': 0.8, 'agemin': 15, 'agemax': 70, 'seek': 0.4,
                                 'rate': 0.3},
                                {'trigger': 'NewSevereCase', 'coverage': 0.8, 'seek': 0.6, 'rate': 0.5}],
                       drug=['Artemether', 'Lumefantrine'],
                       dosing='FullTreatmentNewDetectionTech',
                       nodes={"class": "NodeSetAll"},
                       node_property_restrictions=[],
                       drug_ineligibility_duration=0,
                       duration=-1,
                       repetitions=1,
                       tsteps_btwn_repetitions=365):

    """
    Add a `SimpleHealthSeekingBehavior <http://idmod.org/idmdoc/#EMOD/ParameterReference/SimpleHealthSeekingBehav.htm%3FTocPath%3DParameter%2520Reference|Intervention%2520Parameter%2520Reference|Intervention%2520Parameter%2520Listing|_____53>`_ .

    :param config_builder: The :py:class:`DTKConfigBuilder <dtk.utils.core.DTKConfigBuilder>` containing the campaign configuration
    :param start_day: Day we want to start the intervention
    :param targets: The different targets held in a list of dictionaries (see default for example)
    :param drug: The drug to administer
    :param dosing: The dosing for the drugs
    :param nodes: nodes to target.
    # All nodes: {"class": "NodeSetAll"}.
    # Subset of nodes: {"class": "NodeSetNodeList", "Node_List": list_of_nodeIDs}
    :param node_property_restrictions: used with NodePropertyRestrictions.
    Format: list of dicts: [{ "NodeProperty1" : "PropertyValue1" }, {'NodeProperty2': "PropertyValue2"}, ...]
    :param drug_ineligibility_duration: if this param is > 0, use IndividualProperties to prevent people from receiving
    drugs too frequently. Demographics file will need to define the IP DrugStatus with possible values None and
    RecentDrug. Individuals who receive drugs for treatment will have their DrugStatus changed to RecentDrug for
    drug_ineligibility_duration days. Individuals who already have status RecentDrug will not receive drugs for
    treatment.
    :param duration: how long the intervention lasts
    :param repetitions: Number repetitions
    :param tsteps_btwn_repetitions: Timesteps between the repetitions
    :return:
    """

    expire_recent_drugs['Revert'] = drug_ineligibility_duration

    drug_config, drugs = get_drug_config(drug, dosing, receiving_drugs_event,
                                         drug_ineligibility_duration, expire_recent_drugs)

    for t in targets:

        actual_config = build_actual_treatment_cfg(t['rate'], drug_config, drugs)

        health_seeking_config = {
            "class": "StandardInterventionDistributionEventCoordinator",
            "Number_Repetitions": repetitions,
            "Timesteps_Between_Repetitions": tsteps_btwn_repetitions,
            "Intervention_Config": {
                "class": "NodeLevelHealthTriggeredIV",
                "Trigger_Condition_List": [t['trigger']],
                "Duration": duration,
                # "Tendency": t['seek'],
                "Demographic_Coverage": t['coverage'] * t['seek'],  # to be FIXED later for individual properties
                "Actual_IndividualIntervention_Config": actual_config
            }
        }

        if drug_ineligibility_duration > 0 :
            health_seeking_config['Intervention_Config']["Property_Restrictions_Within_Node"] = [{"DrugStatus": "None"}]

        if node_property_restrictions:
            health_seeking_config['Intervention_Config']['Node_Property_Restrictions'] = node_property_restrictions

        if all([k in t.keys() for k in ['agemin', 'agemax']]):
            health_seeking_config["Intervention_Config"].update({
                "Target_Demographic": "ExplicitAgeRanges",  # Otherwise default is Everyone
                "Target_Age_Min": t['agemin'],
                "Target_Age_Max": t['agemax']})

        health_seeking_event = {"class": "CampaignEvent",
                                "Start_Day": start_day,
                                "Event_Coordinator_Config": health_seeking_config,
                                "Nodeset_Config": nodes}

        config_builder.add_event(health_seeking_event)


def add_health_seeking_by_chw( config_builder,
                               start_day=0,
                               targets={'triggers': ['NewClinicalCase', 'NewSevereCase'],
                                        'coverage': 0.5, 'agemin': 0, 'agemax': 200, 'rate': 0.3},
                               drug=['Artemether', 'Lumefantrine'],
                               dosing='FullTreatmentNewDetectionTech',
                               nodeIDs=[],
                               node_property_restrictions=[],
                               drug_ineligibility_duration=0,
                               duration=100000,
                               chw={}):

    chw_config = {
        'class' : 'CommunityHealthWorkerEventCoordinator',
        'Duration' : duration,
        'Distribution_Rate' : 5,
        'Waiting_Period' : 7,
        'Days_Between_Shipments' : 90,
        'Amount_In_Shipment' : 1000,
        'Max_Stock' : 1000,
        'Initial_Amount_Distribution_Type' : 'FIXED_DURATION',
        'Initial_Amount' : 1000,
        'Target_Demographic' : 'Everyone',
        'Target_Residents_Only' : 0,
        'Demographic_Coverage' : targets['coverage'],
        'Trigger_Condition_List' : targets['triggers'],
        'Property_Restrictions_Within_Node' : []}

    if chw :
        chw_config.update(chw)

    if drug_ineligibility_duration > 0:
        chw_config["Property_Restrictions_Within_Node"].append({"DrugStatus": "None"})

    # NOTE: node property restrictions isn't working yet for CHWEC (3/29/17)
    if node_property_restrictions:
        chw_config['Node_Property_Restrictions'] = node_property_restrictions

    if all([k in targets.keys() for k in ['agemin', 'agemax']]):
        chw_config.update({
            "Target_Demographic": "ExplicitAgeRanges",  # Otherwise default is Everyone
            "Target_Age_Min": targets['agemin'],
            "Target_Age_Max": targets['agemax']})

    expire_recent_drugs['Revert'] = drug_ineligibility_duration
    drug_config, drugs = get_drug_config(drug, dosing, receiving_drugs_event,
                                         drug_ineligibility_duration, expire_recent_drugs)
    actual_config = build_actual_treatment_cfg(targets['rate'], drug_config, drugs)

    chw_config['Intervention_Config'] = actual_config

    nodes = {"class": "NodeSetNodeList", "Node_List": nodeIDs} if nodeIDs else {"class": "NodeSetAll"}

    chw_event = {"class": "CampaignEvent",
                 "Start_Day": start_day,
                 "Event_Coordinator_Config": chw_config,
                 "Nodeset_Config": nodes}

    config_builder.add_event(chw_event)


def get_drug_config(drug, dosing, receiving_drugs_event, drug_ineligibility_duration, expire_recent_drugs) :

    # if drug variable is a list, let's use MultiInterventionDistributor
    if isinstance(drug, basestring):
        # print('Just a single drug: ' + drug)
        drug_config = {"Cost_To_Consumer": 1,
                       "Drug_Type": drug,
                       "Dosing_Type": dosing,
                       "class": "AntimalarialDrug"}
        drugs = drug
    else:
        # print('Multiple drugs: ' + '+'.join(drug))
        drugs = []
        for d in drug:
            drugs.append({"Cost_To_Consumer": 1,
                          "Drug_Type": d,
                          "Dosing_Type": dosing,
                          "class": "AntimalarialDrug"})
        drugs.append(receiving_drugs_event)
        if drug_ineligibility_duration > 0 :
            drugs.append(expire_recent_drugs)
        drug_config = {"class": "MultiInterventionDistributor",
                       "Intervention_List": drugs}

    return drug_config, drugs


def build_actual_treatment_cfg(rate, drug_config, drugs) :

    if rate > 0:
        actual_config = {
            "class": "DelayedIntervention",
            "Coverage": 1.0,
            "Delay_Distribution": "EXPONENTIAL_DURATION",
            "Delay_Period": 1.0 / rate,
            "Actual_IndividualIntervention_Configs": drugs
        }
    else:
        actual_config = drug_config

    return actual_config
