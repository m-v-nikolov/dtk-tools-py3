# Bednet parameters
itn_bednet = { "class": "SimpleBednet",
               "Bednet_Type": "ITN", 
               "Blocking_Rate": 0.9,
               "Killing_Rate": 0.6, 
               "Durability_Time_Profile": "DECAYDURABILITY", 
               "Primary_Decay_Time_Constant":   4 * 365,   # killing
               "Secondary_Decay_Time_Constant": 2 * 365,   # blocking
               "Cost_To_Consumer": 3.75
}

# Bednet distribution event parameters
def add_ITN(config_builder, start, coverage_by_ages, waning={}, cost=None, nodeIDs=[]):

    if waning:
        itn_bednet.update({ "Durability_Time_Profile":       waning['profile'], 
                            "Primary_Decay_Time_Constant":   waning['kill'] * 365,
                            "Secondary_Decay_Time_Constant": waning['block'] * 365 })

    if cost:
        itn_bednet['Cost_To_Consumer'] = cost

    for coverage_by_age in coverage_by_ages:

        ITN_event = { "class" : "CampaignEvent",
                      "Start_Day": start,
                      "Event_Coordinator_Config": {
                          "class": "StandardInterventionDistributionEventCoordinator",
                          "Demographic_Coverage": coverage_by_age["coverage"],
                          "Intervention_Config": itn_bednet
                      }
                    }

        if all([k in coverage_by_age.keys() for k in ['min','max']]):
            ITN_event["Event_Coordinator_Config"].update({
                   "Target_Demographic": "ExplicitAgeRanges",
                   "Target_Age_Min": coverage_by_age["min"],
                   "Target_Age_Max": coverage_by_age["max"]})

        if not nodeIDs:
            ITN_event["Nodeset_Config"] = { "class": "NodeSetAll" }
        else:
            ITN_event["Nodeset_Config"] = { "class": "NodeSetNodeList", "Node_List": nodeIDs }

        if 'birth' in coverage_by_age.keys() and coverage_by_age['birth']:
            birth_triggered_intervention = {
                "class": "BirthTriggeredIV",
                "Duration": -1, # forever.  could expire and redistribute every year with different coverage values
                "Demographic_Coverage": coverage_by_age["coverage"],
                "Actual_IndividualIntervention_Config": itn_bednet
            }
            ITN_event["Event_Coordinator_Config"]["Intervention_Config"] = birth_triggered_intervention
            ITN_event["Event_Coordinator_Config"].pop("Demographic_Coverage")

        config_builder.add_event(ITN_event)
        
def add_ITN_mult (config_builder, campaigns, waning={}, cost=None, nodeIDs=[]):
    
    for campaign in campaigns:
        
        if waning:
            itn_bednet.update({ "Durability_Time_Profile":       waning['profile'], 
                                "Primary_Decay_Time_Constant":   waning['kill'] * 365,
                                "Secondary_Decay_Time_Constant": waning['block'] * 365 })
    
        if cost:
            itn_bednet['Cost_To_Consumer'] = cost
            
        coverage_by_ages = campaign[1]
        start = campaign[0][0]
        #print start
        #print coverage_by_ages
    
        for coverage_by_age in coverage_by_ages:
    
            ITN_event = { "class" : "CampaignEvent",
                          "Start_Day": start,
                          "Event_Coordinator_Config": {
                              "class": "StandardInterventionDistributionEventCoordinator",
                              "Demographic_Coverage": coverage_by_age["coverage"],
                              "Intervention_Config": itn_bednet
                          }
                        }
    
            if all([k in coverage_by_age.keys() for k in ['min','max']]):
                ITN_event["Event_Coordinator_Config"].update({
                       "Target_Demographic": "ExplicitAgeRanges",
                       "Target_Age_Min": coverage_by_age["min"],
                       "Target_Age_Max": coverage_by_age["max"]})
    
            if not nodeIDs:
                ITN_event["Nodeset_Config"] = { "class": "NodeSetAll" }
            else:
                ITN_event["Nodeset_Config"] = { "class": "NodeSetNodeList", "Node_List": nodeIDs }
    
            if 'birth' in coverage_by_age.keys() and coverage_by_age['birth']:
                birth_triggered_intervention = {
                    "class": "BirthTriggeredIV",
                    "Duration": -1, # forever.  could expire and redistribute every year with different coverage values
                    "Demographic_Coverage": coverage_by_age["coverage"],
                    "Actual_IndividualIntervention_Config": itn_bednet
                }
                ITN_event["Event_Coordinator_Config"]["Intervention_Config"] = birth_triggered_intervention
                ITN_event["Event_Coordinator_Config"].pop("Demographic_Coverage")
    
            config_builder.add_event(ITN_event)
        
def construct_milen_ITN_campaign(coverage_level='lowest', burn_in=0) :    

    from dtk.utils.parsers.JSON import json2dict
    nets_calib = json2dict('C:/Users/jgerardin/work/zambia_calibration/itn_trajs_distributions.json')

    nets_campaigns = []

    for coverage, campaign in nets_calib.iteritems():

        if coverage == coverage_level :
        #if coverage != 'data':
            #print "Net campaigns with coverage " + coverage
            for i,eff_dist in enumerate(campaign['best_match']['eff_dists']):
                this_campaign = ((30*(i+1)*campaign['best_match']['period']+burn_in,coverage),\
                                                        [ 
                                                                {'min':0,'max':5,'coverage':eff_dist[0]}, \
                                                                {'min':5,'max':30,'coverage':eff_dist[0] - eff_dist[0]*0.3}, \
                                                                {'min':30,'max':100,'coverage': eff_dist[0]}
                                                        ]
                                                        )
                nets_campaigns.append(this_campaign)

    return nets_campaigns