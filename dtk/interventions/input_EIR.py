def add_InputEIR(cb, monthlyEIRs, age_dependence="SURFACE_AREA_DEPENDENT", start_day=0):
    """
    Create an intervention introducing new infections (see `InputEIR <http://idmod.org/idmdoc/#EMOD/ParameterReference/InputEIR.htm%3FTocPath%3DParameter%2520Reference|Intervention%2520Parameter%2520Reference|Intervention%2520Parameter%2520Listing|_____33>`_ for detail)

    :param cb: The :any:`DTKConfigBuilder` containing the campaign parameters
    :param monthlyEIRs: a list of monthly EIRs (must be 12 items)
    :param age_dependence: "LINEAR" or "SURFACE_AREA_DEPENDENT"
    :param start_day: Start day of the introduction of new infections
    :return: Nothing
    """
    if len(monthlyEIRs) is not 12:
        raise Exception('The input argument monthlyEIRs should have 12 entries, not %d' % len(monthlyEIRs))

    input_EIR_event = { 
            "Event_Name": "Input EIR intervention",
            "Start_Day": start_day,
            "class": "CampaignEvent",
            "Event_Coordinator_Config": 
            { 
                "Number_Repetitions": 1,
                "class": "StandardInterventionDistributionEventCoordinator",
                "Intervention_Config": 
                { 
                    "Age_Dependence": age_dependence,
                    "Monthly_EIR": monthlyEIRs,
                    "class": "InputEIR",
                }
            },
            "Nodeset_Config": 
            { 
                "class": "NodeSetAll"
            }
        }

    cb.add_event(input_EIR_event)