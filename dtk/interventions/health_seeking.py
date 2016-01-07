def add_health_seeking(config_builder,
                       start_day = 0,
                       # Note: potential for overlapping drug treatments in the same individual
                       targets = [ { 'trigger': 'NewClinicalCase', 'coverage': 0.8, 'agemin':15, 'agemax':70, 'seek': 0.4, 'rate': 0.3 },
                                   { 'trigger': 'NewSevereCase',   'coverage': 0.8, 'seek': 0.6, 'rate': 0.5 } ],
                       drug    = ['Artemether', 'Lumefantrine'],
                       dosing  = 'FullTreatmentNewDetectionTech',
                       nodes={"class": "NodeSetAll"}):
    """
    Add a `SimpleHealthSeekingBehavior <http://idmod.org/idmdoc/#EMOD/ParameterReference/SimpleHealthSeekingBehav.htm%3FTocPath%3DParameter%2520Reference|Intervention%2520Parameter%2520Reference|Intervention%2520Parameter%2520Listing|_____53>`_ .

    :param config_builder: The :py:class:`DTKConfigBuilder <dtk.utils.core.DTKConfigBuilder>` containing the campaign configuration
    :param start_day: Day we want to start the intervention
    :param targets: The different targets held in a list of dictionaries (see default for example)
    :param drug: The drug to administer
    :param dosing: The dosing for the drugs
    :return:
    """

    receiving_drugs_event = {
        "class": "BroadcastEvent",
        "Broadcast_Event": "Received_Treatment"
        }

    # if drug variable is a list, let's use MultiInterventionDistributor
    if isinstance(drug, basestring):
        #print('Just a single drug: ' + drug)
        drug_config = { "Cost_To_Consumer": 1, 
                        "Drug_Type": drug,
                        "Dosing_Type": dosing,
                        "class": "AntimalarialDrug" }
    else:
        #print('Multiple drugs: ' + '+'.join(drug))
        drugs=[]
        for d in drug:
            drugs.append({ "Cost_To_Consumer": 1, 
                            "Drug_Type": d,
                            "Dosing_Type": dosing,
                            "class": "AntimalarialDrug" })
        drugs.append(receiving_drugs_event)
        drug_config = { "class": "MultiInterventionDistributor",
                        "Intervention_List": drugs }

    for t in targets:

        if t['rate']>0:
            actual_config={
                    "class": "DelayedIntervention",
                    "Coverage": 1.0,
                    "Delay_Distribution": "EXPONENTIAL_DURATION",
                    "Delay_Period": 1.0/t['rate'],
                    "Actual_IndividualIntervention_Configs": drugs
                 }
        else:
            actual_config=drug_config

        health_seeking_config = { 
            "class": "NodeEventCoordinator",
            "Intervention_Config": {
                "class": "NodeLevelHealthTriggeredIV",
                "Trigger_Condition": t['trigger'], 
                # "Tendency": t['seek'],
                "Demographic_Coverage": t['coverage']*t['seek'],  # to be FIXED later for individual properties
                "Actual_IndividualIntervention_Config": actual_config
             }
        }

        if all([k in t.keys() for k in ['agemin','agemax']]):
            health_seeking_config["Intervention_Config"].update({
                   "Target_Demographic": "ExplicitAgeRanges", # Otherwise default is Everyone
                   "Target_Age_Min": t['agemin'],
                   "Target_Age_Max": t['agemax'] })

        health_seeking_event = { "class": "CampaignEvent",
                                 "Start_Day": start_day,
                                 "Event_Coordinator_Config": health_seeking_config, 
                                 "Nodeset_Config": nodes }

        config_builder.add_event(health_seeking_event)
