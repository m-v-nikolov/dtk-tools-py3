# a class building a config JSON for DTK custom reports
from CustomReportsBucket import CustomReportsBucket
from MalariaReport import MalariaReport
from EventCounterReport import EventCounterReport

class CustomReportsBuilder(object):

    def __init__(self):
        self.malaria_report_types            =  {\
                                                "MalariaImmunityReport", \
                                                "MalariaSummaryReport", \
                                                "MalariaSurveyJSONAnalyzer" \
                                                }

        self.event_counter_report_types      =  {"ReportEventCounter"}

        self.report_buckets = {}

    def get_report_buckets(self):
        return self.report_buckets

    def set_custom_reports(self, report_buckets):
        self.report_buckets = report_buckets

    def add_report_bucket(self, report_bucket):
        bucket_type = report_bucket.get_type()
        self.report_buckets[bucket_type] = report_bucket
 

    ''' given a dictionary of custom report types (i.e. custom_report_types) with keys types and values number of reports 
        to be generated per report type, build a set of buckets each containing num custom reports of each type, 
        the reports' parameters are generated using default values. 

        currently supported custom report types:
        
        ReportEventCounter
        MalariaImmunityReport
        MalariaSummaryReport
        MalariaSurveyJSONAnalyzer
    '''    
    def generate_default_custom_reports(self, custom_report_types):
        for (custom_report_type, num) in custom_report_types.iteritems():
            custom_report_bucket = CustomReportsBucket(custom_report_type, 1)
            if custom_report_type in self.malaria_report_types:
                for i in range(num):
                    malaria_report = MalariaReport(event_trigger_list = ["EveryUpdate"], type = custom_report_type)
                    custom_report_bucket.add_custom_report(malaria_report)
            elif custom_report_type in self.event_counter_report_types:
                for i in range(num):
                    event_counter_report = EventCounterReport(event_trigger_list =    [\
                                                                                        "Births",\
                                                                                        "EveryUpdate",\
                                                                                        "EveryTimeStep",\
                                                                                        "NewInfectionEvent",\
                                                                                        "NewClinicalCase",\
                                                                                        "NewSevereCase",\
                                                                                        "DiseaseDeaths",\
                                                                                        "NonDiseaseDeaths",\
                                                                                        "PropertyChange"\
                                                                                        ])
                    custom_report_bucket.add_custom_report(event_counter_report)
            else:
                raise Exception("Unknown report type!")
            
            self.add_report_bucket(custom_report_bucket)
            custom_report_bucket = None


    def custom_reports_config_DTK(self):
        reportsJSON = {}
        reportsJSON["Custom_Reports"] = {}
        for report_bucket in self.report_buckets.itervalues():
            bucket_type = report_bucket.get_type()
            bucket_enabled = report_bucket.get_enabled()
            reportsJSON["Custom_Reports"][bucket_type] = {}
            reportsJSON["Custom_Reports"][bucket_type]["Enabled"] = bucket_enabled
            reportsJSON["Custom_Reports"][bucket_type]["Reports"] = report_bucket.bucket_config_DTK()
        return reportsJSON