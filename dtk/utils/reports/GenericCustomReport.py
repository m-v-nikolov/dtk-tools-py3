# a class representing a generic custom report configuration
class GenericCustomReport(object):

    def __init__(self, \
        event_trigger_list, \
        start_day = 0, \
        duration_days = 10000, \
        report_description = "", \
        nodeset_config = {"class":"NodeSetAll"}, \
        type = "" \
        ):

        self.start_day = start_day
        self.duration_days = duration_days
        self.report_description = report_description
        self.nodeset_config = nodeset_config
        self.event_trigger_list = event_trigger_list

        self.type = type

    ''' providing mutators and accessors in case we'd like to work with 
    views of reporter configs (e.g. in the cointext of a GUI or other configuration tool) in the future
    '''

    #report attributes accessors
    def get_start_day(self):
        return self.start_day  

    def get_duration_days(self):
        return self.duration_days

    def get_report_description(self):
        return self.report_description

    def get_nodeset_config(self):
        return self.nodeset_config

    def get_event_triggerList(self):
        return self.event_trigger_list

    def get_type(self):
        return self.type

    #report attributes mutators
    def set_start_day(self, start_day):
        self.start_day  = start_day

    def set_duration_days(self, duration_day):
        self.duration_days = duration_day

    def set_report_description(self, report_description):
        self.report_description = report_description

    def set_nodeset_config(self, nodeset_config):
        self.nodeset_config = nodeset_config

    def set_event_trigger_list(self, event_trigger_list):
        self.event_trigger_list = event_trigger_list

    def set_type(self, type):
        self.type = type

    def report_config_DTK(self):
        return {
                "Start_Day":self.start_day, \
                "Duration_Days":self.duration_days, \
                "Report_Description":self.report_description, \
                "Nodeset_Config":self.nodeset_config, \
                "Event_Trigger_List":self.event_trigger_list \
                }