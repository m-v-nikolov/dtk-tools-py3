from dtk.utils.reports.MalariaReport import MalariaReport

def add_survey_report(cb, 
                      survey_days, 
                      reporting_interval=21, 
                      trigger=["EveryUpdate"], 
                      nreports=1, 
                      include_births=False, 
                      coverage=1):

    survey_report = [MalariaReport(event_trigger_list=trigger,
                                    start_day = survey_day,
                                    coverage = coverage,
                                    include_births =  include_births,
                                    max_number_reports = nreports,
                                    reporting_interval = reporting_interval,
                                    report_description = 'Day_' + str(survey_day),
                                    type = "MalariaSurveyJSONAnalyzer" ) for survey_day in survey_days]

    return survey_report
