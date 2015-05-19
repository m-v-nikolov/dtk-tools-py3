import copy

# Ivermectin parameters
ivermectin_cfg = { "class": "Ivermectin",
                   "Killing_Config": { "class": "WaningEffectBox",
                                       "Box_Duration": 1,
                                       "Initial_Effect": 0.95 },
                   "Cost_To_Consumer": 15.0 }

def ivermectin_config_by_duration(drug_code=None):
    if not drug_code:
        return {}
    cfg=copy.deepcopy(ivermectin_cfg)
    if drug_code == 'DAY':
        cfg['Killing_Config']['Box_Duration'] = 1
    elif drug_code == 'WEEK':
        cfg['Killing_Config']['Box_Duration'] = 7
    elif drug_code == 'MONTH':
        cfg['Killing_Config']['Box_Duration'] = 30
    else:
        raise Exception("Don't recognize drug_code" % drug_code)
    return cfg

# IVM distribution event parameters
def add_ivermectin(config_builder, drug_code, coverage, start_days):

    cfg=ivermectin_config_by_duration(drug_code)

    for start_day in start_days:
        IVM_event = { "class" : "CampaignEvent",
                      "Start_Day": start_day,
                      "Event_Coordinator_Config": {
                          "class": "StandardInterventionDistributionEventCoordinator",
                          "Demographic_Coverage": coverage,
                          "Intervention_Config": cfg
                      }
                    }

        IVM_event["Nodeset_Config"] = { "class": "NodeSetAll" }

        config_builder.add_event(IVM_event)