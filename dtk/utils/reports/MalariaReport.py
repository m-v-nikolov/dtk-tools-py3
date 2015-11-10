from CustomReport import BaseReport, BaseEventReportIntervalOutput

class MalariaReport(BaseEventReportIntervalOutput):

    dlls = {'MalariaSummaryReport': 'libmalariasummary_report_plugin.dll',
            'MalariaImmunityReport': 'libmalariaimmunity_report_plugin.dll'}

    def __init__(self,
                 event_trigger_list,
                 start_day = 0,
                 duration_days = 1000000,
                 report_description = "",
                 nodeset_config = {"class":"NodeSetAll"},
                 age_bins =  [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 1000 ],
                 max_number_reports = 15,
                 reporting_interval = 73,
                 type = ""):

        BaseEventReportIntervalOutput.__init__(self, event_trigger_list, start_day, duration_days, 
                                     report_description, nodeset_config, max_number_reports,reporting_interval,type)
        self.age_bins = age_bins

    def to_dict(self):
        d = super(MalariaReport, self).to_dict()
        d["Age_Bins"] = self.age_bins
        return d

default_age_bins=[ 1.0/12, 0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
                   11, 12, 13, 14, 15, 20, 25, 30, 40,  50,  60, 1000 ]

def add_summary_report(cb, start=0, interval=365, nreports=10000, 
                       description = 'AnnualAverage', 
                       age_bins = default_age_bins):

    summary_report = MalariaReport(event_trigger_list=['EveryUpdate'],
                                   start_day = start,
                                   report_description = description,
                                   age_bins =  age_bins,
                                   max_number_reports = nreports,
                                   reporting_interval = interval)
    summary_report.type="MalariaSummaryReport"
    cb.add_reports(summary_report)

def add_immunity_report(cb, start=0, interval=365, nreports=10000, 
                       description = 'AnnualAverage', 
                       age_bins = default_age_bins):

    immunity_report = MalariaReport(event_trigger_list=['EveryUpdate'],
                                   start_day = start,
                                   report_description = description,
                                   age_bins =  age_bins,
                                   max_number_reports = nreports,
                                   reporting_interval = interval)
    immunity_report.type="MalariaImmunityReport"
    cb.add_reports(immunity_report)

def add_survey_report(cb, survey_days, reporting_interval=21, 
                      trigger=["EveryUpdate"], nreports=1):

    survey_reports = [BaseEventReportIntervalOutput(
                          event_trigger_list=trigger,
                          start_day = survey_day,
                          max_number_reports = nreports,
                          reporting_interval = reporting_interval,
                          report_description = 'Day_' + str(survey_day),
                          type = "MalariaSurveyJSONAnalyzer" ) for survey_day in survey_days]
    cb.add_reports(*survey_reports)

def add_patient_report(cb):
    cb.add_reports(BaseReport(type="MalariaPatientJSONReport"))
