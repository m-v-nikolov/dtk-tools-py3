# a class to store a list of custom reports of particular type (e.g. MalariaImmunityReport, MalariaSummaryReport, etc.)

class CustomReportsBucket(object):

    def __init__(self, type, enabled=1):
        self.type = type
        self.enabled = enabled
        self.custom_reports = []
        
    #reports bucket attributes accessors
    def get_type(self):
        return self.type

    def get_enabled(self):
        return self.enabled

    def get_custom_reports(self):
        return self.custom_reports

    #reports bucket attributes mutators
    def set_type(self, type):
        self.type  = type

    def set_enabled(self, enabled):
        self.enabled = enabled

    def set_custom_reports(self, custom_reports):
        self.custom_reports = custom_reports

    def add_custom_report(self, custom_report):
        if custom_report.get_type() == self.type:
            self.custom_reports.append(custom_report)
        else: 
            raise Exception("Report type does not match bucket type")

    def bucket_config_DTK(self):
        reportsJSON = []
        for custom_report in self.custom_reports:
            reportsJSON.append(custom_report.report_config_DTK())  
        return reportsJSON  


