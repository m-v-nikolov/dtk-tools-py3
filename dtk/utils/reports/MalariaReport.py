''' a class representing a Malaria custom report configuration 
    (could be used for immunity reports, summary reports, JSON Analyzer Reports, etc.);
    this class inherits from class CustomReportGeneric; 
    If in the future we need to distinguish the config attributes across different Malaria reports,
    we can have classes inheritting this MalariaReport class
'''

from GenericCustomReport import GenericCustomReport

class MalariaReport(GenericCustomReport):

    def __init__(self, \
        event_trigger_list, \
        start_day = 0, \
        duration_days = 10000, \
        report_description = "", \
        nodeset_config = {"class":"NodeSetAll"}, \
        age_bins =  [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 1000 ], \
        max_number_reports = 15, \
        reporting_interval = 73, \
        type = "" \
        ):
        GenericCustomReport.__init__(self, event_trigger_list, start_day, duration_days, report_description, nodeset_config, type)

        self.age_bins = age_bins
        self.max_number_reports = max_number_reports
        self.reporting_interval = reporting_interval
    
    # report attributes accessors    
    def get_age_bins(self):
        return self.age_bins

    def get_max_number_reports(self):
        return self.max_number_reports

    def get_reporting_interval(self):
        return self.reporting_interval

    #report attributes mutators
    def set_age_bins(self, age_bins):
        self.age_bins  = age_bins

    def set_max_number_reports(self, max_number_reports):
        self.max_number_reports = max_number_reports

    def set_reporting_interval(self, reporting_interval):
        self.reporting_interval = reporting_interval

    def report_config_DTK(self):    
        reportJSON = super(MalariaReport, self).report_config_DTK()
        reportJSON["Max_Number_Reports"] = self.max_number_reports
        reportJSON["Reporting_Interval"] = self.reporting_interval
        reportJSON["Age_Bins"] = self.age_bins

        return reportJSON

