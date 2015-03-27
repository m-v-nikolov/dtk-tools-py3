# Ivermectin parameters
ivermectin = { "class": "Ivermectin",
               "Killing_Rate": 0.95, 
               "Durability_Time_Profile": "BOXDURABILITY", 
               "Primary_Decay_Time_Constant":   0.9,  # box
               "Cost_To_Consumer": 15.0
}

# IVM distribution event parameters
def add_ivermectin(config_builder, drug_code, coverage, start_days):

    if drug_code == 'DAY':
        ivermectin['Primary_Decay_Time_Constant'] = 1
    elif drug_code == 'WEEK':
        ivermectin['Primary_Decay_Time_Constant'] = 7
    elif drug_code == 'MONTH':        
        ivermectin['Primary_Decay_Time_Constant'] = 30
    else:
        raise Exception("Don't recognize drug_code" % drug_code)

    for start_day in start_days:
        IVM_event = { "class" : "CampaignEvent",
                      "Start_Day": start_day,
                      "Event_Coordinator_Config": {
                          "class": "StandardInterventionDistributionEventCoordinator",
                          "Demographic_Coverage": coverage,
                          "Intervention_Config": ivermectin
                      }
                    }

        IVM_event["Nodeset_Config"] = { "class": "NodeSetAll" }

        config_builder.add_event(IVM_event)