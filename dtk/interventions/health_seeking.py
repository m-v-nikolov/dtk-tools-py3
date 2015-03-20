def add_health_seeking(config_builder,
                       start_day = 0,
                       # Note: potential for overlapping drug treatments in the same individual
                       targets = [ { 'trigger': 'NewClinicalCase', 'coverage': 0.8, 'agemin':15, 'agemax':70, 'seek': 0.4, 'rate': 0.3 },
                                   { 'trigger': 'NewSevereCase',   'coverage': 0.8, 'seek': 0.6, 'rate': 0.5 } ],
                       drug    = 'Artemether_Lumefantrine',
                       dosing  = 'FullTreatmentNewDetectionTech'):



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
        drug_config = { "class": "MultiInterventionDistributor",
                        "Intervention_List": drugs }

    for t in targets:

        if t['rate']>0:
            actual_config={
                    "class": "SimpleHealthSeekingBehavior",
                    "Tendency": t['rate'],
                    "Actual_IndividualIntervention_Config": drug_config
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
                                           "Target_Age_Min": t['agemin'],
                                           "Target_Age_Max": t['agemax'] })

        health_seeking_event = { "class": "CampaignEvent",
                                 "Start_Day": start_day,
                                 "Event_Coordinator_Config": health_seeking_config, 
                                 "Nodeset_Config": { "class": "NodeSetAll" } }

        config_builder.add_event(health_seeking_event)
