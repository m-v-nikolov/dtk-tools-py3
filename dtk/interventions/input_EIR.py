# Recurring introduction of new infections
def add_InputEIR(cb, monthlyEIRs, age_dependence="SURFACE_AREA_DEPENDENT", start_day=0):

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

    return cb
