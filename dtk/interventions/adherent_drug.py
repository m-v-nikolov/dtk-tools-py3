import random
from triggered_campaign_delay_event import triggered_campaign_delay_event


def add_adherent_drug(config_builder, start=1, coverage=1, cost=1, nodeIDs=[], number_repetitions=1,
                      timesteps_between_repititions=0, drug_type="DHA", dont_allow_duplicates=1,
                      dosing_type="FullTreatmentCourse", adherence_config={}, non_adherence_options=["NEXT_UPDATE"],
                      non_adherence_distribution=[1], max_dose_consideration_duration=40, took_dose_event="Took_Dose",
                      ind_property_restrictions=[], node_property_restrictions=[],
                      triggered_campaign_delay=0, trigger_condition_list=[], listening_duration=-1):
    """
    :param config_builder: The :py:class:`DTKConfigBuilder <dtk.utils.core.DTKConfigBuilder>` holding the campaign that will receive the IRS event
    :param start: The start day of the spraying
    :param coverage: percentage of everyone covered by the campaign
    :param cost: Set the ``Cost_To_Consumer`` parameter
    :param nodeIDs: If empty, all nodes will get the intervention. If set, only the nodeIDs specified will receive the intervention.
    :param number_repetitions: how many times you want to this event to repeat
    :param timesteps_between_repititions: how many time steps between repeating the event
    :param drug_type: name of the drug, matching a defined drug in the config file under Malaria_Drug_Params
    :param dosing_type: currently, this is one of the DrugUsageType enums, but might change in the future
    :param adherence_config: a dictionary defining WaningEffects or WaningEffectCombo
    ex:  {
        "class" : "WaningEffectCombo",
        "Effect_List" : [
            {
                "class": "WaningEffectMapLinearAge",
                "Initial_Effect" : 1.0,
                "Durability_Map" :
                {
                    "Times"  : [ 0.0,  12.99999,  13.0, 125.0 ],
                    "Values" : [ 0.0,   0.0,       1.0,   1.0 ]
                }
            },
            {
                "class": "WaningEffectMapCount",
                "Initial_Effect" : 1.0,
                "Durability_Map" :
                {
                    "Times"  : [ 1.0, 2.0, 3.0 ],
                    "Values" : [ 0.9, 0.7, 0.5 ]
                }
            },
            {
                "class": "WaningEffectExponential",
                "Initial_Effect": 1.0,
                "Decay_Time_Constant" : 7
            }
        ]
    }
    :param non_adherence_options:  This is an array of enums where each enum defines what happens when the user is not adherent.
            if empty, NEXT_UPDATE is used. options: ["STOP", "NEXT_UPDATE", "NEXT_DOSAGE_TIME", "LOST_TAKE_NEXT"]
    :param non_adherence_distribution:  An array of probabilities. There must be one value in this array for each value
            in non_adherence_options. The sum of these values must equal 1.0.
    :param max_dose_consideration_duration: Max_Dose_Consideration_Duration The maximum number of days that an individual will  consider taking the doses of the drug
    :param ind_property_restrictions: Restricts irs based on list of individual properties in format [{"BitingRisk":"High"}, {"IsCool":"Yes}]
    :param node_property_restrictions: restricts irs based on list of node properties in format [{"Place":"RURAL"}, {"ByALake":"Yes}]
    :param triggered_campaign_delay: how many time steps after receiving the trigger will the campaign start.
    Eligibility of people or nodes for campaign is evaluated on the start day, not the triggered day.
    :param trigger_condition_list: when not empty,  the start day is the day to start listening for the trigger conditions listed, distributing the spraying
        when the trigger is heard. This does not distribute the BirthTriggered intervention.
    :param listening_duration: how long the distributed event will listen for the trigger for, default is -1, which is indefinitely
    :return: Nothing
    """
    # built-in default so we can run this function by just putting in the config builder.
    if not adherence_config:
        adherence_config = {
            "class": "WaningEffectMapLinearAge",
            "Initial_Effect": 1.0,
            "Durability_Map":
                {
                    "Times": [0.0, 12.99999, 13.0, 125.0],
                    "Values": [0.0, 0.0, 1.0, 1.0]
                }
        }

    adherent_drug = {
        "class": "AdherentDrug",
        "Dont_Allow_Duplicates": dont_allow_duplicates,
        "Cost_To_Consumer": cost,
        "Drug_Type": drug_type,
        "Dosing_Type": dosing_type,
        "Adherence_Config": adherence_config,
        "Non_Adherence_Options": non_adherence_options,
        "Non_Adherence_Distribution": non_adherence_distribution,
        "Max_Dose_Consideration_Duration": max_dose_consideration_duration,
        "Took_Dose_Event": took_dose_event
    }

    if not nodeIDs:
        nodeset_config = {"class": "NodeSetAll"}
    else:
        nodeset_config = {"class": "NodeSetNodeList", "Node_List": nodeIDs}

    if trigger_condition_list:
        if number_repetitions > 1 or triggered_campaign_delay > 0:
            event_to_send_out = random.randrange(100000)
            for x in range(number_repetitions):
                # create a trigger for each of the delays.
                triggered_campaign_delay_event(config_builder, start, nodeIDs,
                                               triggered_campaign_delay + x * timesteps_between_repititions,
                                               trigger_condition_list,
                                               listening_duration, event_to_send_out)
            trigger_condition_list = [str(event_to_send_out)]

        adherent_event = {
                 "class": "CampaignEvent",
                 "Start_Day": int(start),
                 "Nodeset_Config": nodeset_config,
                 "Event_Coordinator_Config": {
                     "class": "StandardInterventionDistributionEventCoordinator",
                     "Intervention_Config": {
                         "class": "NodeLevelHealthTriggeredIV",
                         "Trigger_Condition_List": trigger_condition_list,
                         "Duration": listening_duration,
                         "Property_Restrictions_Within_Node": ind_property_restrictions,
                         "Node_Property_Restrictions": node_property_restrictions,
                         "Demographic_Coverage": coverage,
                         "Target_Residents_Only": 1,
                         "Actual_IndividualIntervention_Config": adherent_drug
                         }
                    }
                 }

    else:
        adherent_event = {
                     "class": "CampaignEvent",
                     "Start_Day": int(start),
                     "Nodeset_Config": nodeset_config,
                     "Event_Coordinator_Config": {
                         "class": "StandardInterventionDistributionEventCoordinator",
                         "Demographic_Coverage": coverage,
                         "Number_Repetitions": number_repetitions,
                         "Timesteps_Between_Repetitions": timesteps_between_repititions,
                         "Target_Residents_Only": 1,
                         "Property_Restrictions_Within_Node": ind_property_restrictions,
                         "Node_Property_Restrictions": node_property_restrictions,
                         "Intervention_Config": adherent_drug
                          }
                     }

    config_builder.add_event(adherent_event)

