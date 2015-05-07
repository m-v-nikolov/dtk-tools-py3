import os

from dtk.utils.core.DTKSetupParser import DTKSetupParser

def format(reports):
    reportsJSON={'Custom_Reports':{'Use_Explicit_Dlls':1}}
    types=set([r.type for r in reports])
    buckets={t:{'Enabled':1,'Reports':[]} for t in types}
    for r in reports:
        buckets[r.type]['Reports'].append(r.to_dict())
    reportsJSON['Custom_Reports'].update(buckets)
    return reportsJSON

class BaseReport(object):

    dlls = {'MalariaPatientJSONReport': 'libmalariapatientJSON_report_plugin.dll'}

    dll_root = DTKSetupParser().get('BINARIES', 'dll_path')

    def __init__(self, type = ""):
        self.type = type

    def to_dict(self):
        return {}

    def get_dll_path(self):
        dll=self.dlls.get(self.type,None)
        if dll:
            return os.path.join(self.dll_root,'reporter_plugins',dll)
        else:
            raise Exception('No known DLL for report type %s'%self.type)

class BaseEventReport(BaseReport):

    def __init__(self,
                 event_trigger_list,
                 start_day = 0,
                 duration_days = 10000,
                 report_description = "",
                 nodeset_config = {"class":"NodeSetAll"},
                 type = ""):

        BaseReport.__init__(self, type)
        self.start_day = start_day
        self.duration_days = duration_days
        self.report_description = report_description
        self.nodeset_config = nodeset_config
        self.event_trigger_list = event_trigger_list

    def to_dict(self):
        return {"Start_Day":self.start_day,
                "Duration_Days":self.duration_days,
                "Report_Description":self.report_description,
                "Nodeset_Config":self.nodeset_config,
                "Event_Trigger_List":self.event_trigger_list}

class BaseEventReportIntervalOutput(BaseEventReport):

    dlls = {'MalariaSurveyJSONAnalyzer': 'libmalariasurveyJSON_analyzer_plugin.dll'}

    def __init__(self,
                 event_trigger_list,
                 start_day = 0,
                 duration_days = 10000,
                 report_description = "",
                 nodeset_config = {"class":"NodeSetAll"},
                 max_number_reports = 15,
                 reporting_interval = 73,
                 type = ""):

        BaseEventReport.__init__(self, event_trigger_list, start_day, duration_days, 
                                     report_description, nodeset_config, type)
        self.max_number_reports = max_number_reports
        self.reporting_interval = reporting_interval

    def to_dict(self):
        d = super(BaseEventReportIntervalOutput, self).to_dict()
        d["Max_Number_Reports"] = self.max_number_reports
        d["Reporting_Interval"] = self.reporting_interval
        return d