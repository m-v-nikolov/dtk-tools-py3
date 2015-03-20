''' a class representing an event counter custom report configuration;
    this class inherits from class CustomReportGeneric; 
'''
from GenericCustomReport import GenericCustomReport

class EventCounterReport(GenericCustomReport):

    def __init__(self, \
        event_trigger_list, \
        start_day = 0, \
        duration_days = 10000, \
        report_description = "", \
        nodeset_config = {"class":"NodeSetAll"}, \
        ):

        # at present EventCounterReport and GenericCustomReports have the same attributes
        GenericCustomReport.__init__(self, event_trigger_list, start_day, duration_days, report_description, nodeset_config, type="ReportEventCounter")

        def report_config_DTK(self):
            # just call the generic report configuration export since no changes are required to it at present for EventCounterReport
            return super(EventCounterReport, self).report_config_DTK()
