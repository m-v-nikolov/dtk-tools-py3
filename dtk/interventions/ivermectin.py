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

    :param drug_code: Can be ``'DAY'``, ``'WEEK'`` or ``'MONTH'`` or a number of days and drive the ``Killing_config`` (see `Killing_Config in Ivermectin <https://institutefordiseasemodeling.github.io/EMOD/malaria/parameter-campaign.html#iv-ivermectin>`_ for more info).
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


def add_ivermectin(config_builder, drug_code, coverage, start_days, trigger_string_list=[]):
    """
    Add an ivermectin event to the config_builder passed.

    :param config_builder: The config builder getting the intervention event
    :param drug_code: Can be 'DAY', 'WEEK' or 'MONTH' and drive the ``Killing_config`` (see `Killing_Config in Ivermectin <https://institutefordiseasemodeling.github.io/EMOD/malaria/parameter-campaign.html#iv-ivermectin>`_ for more info).
    :param coverage: Set the ``Demographic_Coverage``
    :param start_days: list of days when to start the ivermectin distribution
    :param trigger_string_list: ivermectin will be distributed when it hears the trigger string event, please note the start_days then is used to distribute the NodeLevelHealthTriggeredIV
    :return: Nothing
    """

    cfg=ivermectin_config_by_duration(drug_code)

    for start_day in start_days:
        IVM_event = {"class": "CampaignEvent",
                     "Start_Day": start_day,
                     "Event_Coordinator_Config": {
                        "class": "StandardInterventionDistributionEventCoordinator"

                    },
                     "Nodeset_Config": {"class": "NodeSetAll"}}

        if trigger_string_list:
            IVM_event['Event_Coordinator_Config']['Intervention_Config'] = {
                "class" : "NodeLevelHealthTriggeredIV",
                "Trigger_Condition_List": trigger_string_list,
                "Target_Residents_Only": 1,
                "Demographic_Coverage": coverage,
                "Actual_IndividualIntervention_Config" : cfg
            }
        else:
            IVM_event['Event_Coordinator_Config'].update( {
                "Target_Residents_Only": 1,
                "Demographic_Coverage": coverage,
                'Intervention_Config' : cfg
            })

        config_builder.add_event(IVM_event)