import copy

# Ivermectin parameters
ivermectin_cfg = { "class": "Ivermectin",
                   "Killing_Config": { "class": "WaningEffectBox",
                                       "Box_Duration": 1,
                                       "Initial_Effect": 0.95 },
                   "Cost_To_Consumer": 15.0 }

def ivermectin_config_by_duration(drug_code=None):
    """
    Returns the correct ``Killing_Config`` parameter depending on the ``drug_code``

    :param drug_code: Can be ``'DAY'``, ``'WEEK'`` or ``'MONTH'`` or a number of days and drive the ``Killing_config`` (see `Killing config doc <http://idmod.org/idmdoc/#EMOD/ParameterReference/Killing_Config.htm%3FTocPath%3DParameter%2520Reference|Intervention%2520Parameter%2520Reference|Intervention%2520Parameter%2520Listing|Ivermectin|_____1>`_ for more info).
    :return: a dictionary with the correct ``Killing_Config / Box_Duration`` set.
    """
    if not drug_code:
        return {}
    cfg=copy.deepcopy(ivermectin_cfg)
    if isinstance(drug_code, str):
        if drug_code == 'DAY':
            cfg['Killing_Config']['Box_Duration'] = 1
        elif drug_code == 'WEEK':
            cfg['Killing_Config']['Box_Duration'] = 7
        elif drug_code == 'MONTH':
            cfg['Killing_Config']['Box_Duration'] = 30
        else:
            raise Exception("Don't recognize drug_code" % drug_code)
    elif isinstance(drug_code, (int, float)):
        cfg['Killing_Config']['Box_Duration'] = drug_code
    else:
        raise Exception("Drug code should be the IVM duration in days or a string like 'DAY', 'WEEK', 'MONTH'")

    return cfg


def add_ivermectin(config_builder, drug_code, coverage, start_days):
    """
    Add an ivermectin event to the config_builder passed.

    :param config_builder: The config builder getting the intervention event
    :param drug_code: Can be 'DAY', 'WEEK' or 'MONTH' and drive the ``Killing_config`` (see `Killing config doc <http://idmod.org/idmdoc/#EMOD/ParameterReference/Killing_Config.htm%3FTocPath%3DParameter%2520Reference|Intervention%2520Parameter%2520Reference|Intervention%2520Parameter%2520Listing|Ivermectin|_____1>`_ for more info).
    :param coverage: Set the ``Demographic_Coverage``
    :param start_days: list of days when to start the ivermectin distribution
    :return: Nothing
    """

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