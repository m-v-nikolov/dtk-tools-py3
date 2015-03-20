# Test a survey analyzer distribution
def add_survey(campaign, survey_days, reporting_interval=21, trigger="EveryUpdate", nreports=1, include_births=False, coverage=1):

    for start_day in survey_days:
        # Survey parameters
        survey_config = { "class": "MalariaSurveyJSONAnalyzer",
                         #"class": "MalariaSurveyAnalyzer",
                          "Coverage": coverage,
                          "Include_Births": int(include_births),
                          "Reporting_Interval": reporting_interval,
                          "Number_Reports": nreports,
                          "Report_Description": "Day" + str(start_day),
                          "Trigger_Condition": trigger # "NewInfectionEvent", "EveryTimeStep", "EveryUpdate"
                       }

        # Survey distribution event parameters
        survey_event = { "class" : "CampaignEvent",
                      "Start_Day": start_day,
                      "Event_Coordinator_Config": {
                          "class": "StandardInterventionDistributionEventCoordinator",
                          "Intervention_Config": survey_config
                         },
                      "Nodeset_Config": {
                        "class": "NodeSetAll"
                        }
                    }
        campaign["Events"].append(survey_event)

    campaign["Campaign_Name"] = "Malaria Survey Analyzer"
    return campaign
