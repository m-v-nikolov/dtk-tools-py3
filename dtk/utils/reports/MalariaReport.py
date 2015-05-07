from CustomReport import CustomReport

class MalariaReport(CustomReport):
    ''' A class representing a Malaria custom report configuration.
        Could be used for immunity, summary, survey reports, etc.
        This class inherits from class CustomReport.
    '''

    dlls = {'MalariaSummaryReport': 'libmalariasummary_report_plugin.dll',
            'MalariaImmunityReport': 'libmalariaimmunity_report_plugin.dll',
            'MalariaSurveyJSONAnalyzer': 'libmalariasurveyJSON_analyzer_plugin.dll',
            'MalariaPatientJSONReport': 'libmalariapatientJSON_report_plugin.dll'
            }

    def __init__(self,
                 event_trigger_list,
                 start_day = 0,
                 duration_days = 10000,
                 report_description = "",
                 nodeset_config = {"class":"NodeSetAll"},
                 age_bins =  [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 1000 ],
                 max_number_reports = 15,
                 reporting_interval = 73,
                 type = ""):

        CustomReport.__init__(self, event_trigger_list, start_day, duration_days, 
                                     report_description, nodeset_config, type)
        
        self.age_bins = age_bins
        self.max_number_reports = max_number_reports
        self.reporting_interval = reporting_interval

    def to_dict(self):
        d = super(MalariaReport, self).to_dict()
        d["Max_Number_Reports"] = self.max_number_reports
        d["Reporting_Interval"] = self.reporting_interval
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

def add_survey_report(cb, 
                      survey_days, 
                      reporting_interval=21, 
                      trigger=["EveryUpdate"], 
                      nreports=1, 
                      include_births=False, 
                      coverage=1):

    survey_reports = [MalariaReport(event_trigger_list=trigger,
                                    start_day = survey_day,
                                    #coverage = coverage,
                                    #include_births =  include_births,
                                    max_number_reports = nreports,
                                    reporting_interval = reporting_interval,
                                    report_description = 'Day_' + str(survey_day),
                                    type = "MalariaSurveyJSONAnalyzer" ) for survey_day in survey_days]
    cb.add_reports(*survey_reports)
