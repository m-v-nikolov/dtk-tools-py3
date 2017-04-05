def format(reports):
    reports_json = {'Custom_Reports': {'Use_Explicit_Dlls': 1}}
    types = set([r.type for r in reports])
    buckets = {t: {'Enabled': 1, 'Reports': []} for t in types}
    for r in reports:
        buckets[r.type]['Reports'].append(r.to_dict())
        reports_json['Custom_Reports'].update(buckets)
    return reports_json


class BaseReport(object):

    dlls = {'MalariaPatientJSONReport': 'libmalariapatientJSON_report_plugin.dll',
            'VectorHabitatReport': 'libvectorhabitat_report_plugin.dll',
            'ReportVectorStats': 'libvectorstats.dll',
            'ReportVectorMigration': 'libvectormigration.dll',
            'ReportHumanMigrationTracking': 'libhumanmigrationtracking.dll',
            'ReportEventCounter': 'libreporteventcounter.dll',
            'ReportMalariaFiltered': 'libReportMalariaFiltered.dll',
            'SpatialReportMalariaFiltered': 'libSpatialReportMalariaFiltered.dll'
            }

    def __init__(self, type=""):
        self.type = type

    def to_dict(self):
        try:
            d = dict(Pretty_Format=self.pretty_format)
        except AttributeError:
            d = dict()
        return d

    def get_dll_path(self):
        dll = self.dlls.get(self.type, None)
        if dll:
            return 'reporter_plugins', dll
        else:
            raise Exception('No known DLL for report type %s' % self.type)


class BaseDemographicsReport(BaseReport):

    dlls = {'ReportNodeDemographics': 'libReportNodeDemographics.dll'}

    def __init__(self,
                 stratify_by_gender=0,
                 age_bins=[],
                 IP_key_to_collect="",
                 type=""):

        BaseReport.__init__(self, type)
        self.stratify_by_gender = stratify_by_gender
        self.age_bins = age_bins
        self.IP_key_to_collect = IP_key_to_collect

    def to_dict(self):
        d = super(BaseDemographicsReport, self).to_dict()
        d.update({"Stratify_By_Gender": self.stratify_by_gender,
                  "Age_Bins": self.age_bins})
        if self.IP_key_to_collect:
            d.update({"IP_Key_To_Collect": self.IP_key_to_collect})
        return d


class BaseEventReport(BaseReport):

    dlls = {'MalariaTransmissionReport': 'libReportMalariaTransmissions.dll',
            'ReportEventCounter': 'libreporteventcounter.dll'}

    def __init__(self,
                 event_trigger_list,
                 start_day=0,
                 duration_days=1000000,
                 report_description="",
                 nodeset_config={"class": "NodeSetAll"},
                 type=""):

        BaseReport.__init__(self, type)
        self.start_day = start_day
        self.duration_days = duration_days
        self.report_description = report_description
        self.nodeset_config = nodeset_config
        self.event_trigger_list = event_trigger_list

    def to_dict(self):
        d = super(BaseEventReport, self).to_dict()
        d.update({"Start_Day": self.start_day,
                  "Duration_Days": self.duration_days,
                  "Report_Description": self.report_description,
                  "Nodeset_Config": self.nodeset_config,
                  "Event_Trigger_List": self.event_trigger_list})
        return d


class BaseEventReportIntervalOutput(BaseEventReport):

    dlls = {'MalariaSurveyJSONAnalyzer': 'libmalariasurveyJSON_analyzer_plugin.dll'}

    def __init__(self,
                 event_trigger_list,
                 start_day=0,
                 duration_days=1000000,
                 report_description="",
                 nodeset_config={"class": "NodeSetAll"},
                 max_number_reports=15,
                 reporting_interval=73,
                 type=""):

        BaseEventReport.__init__(self, event_trigger_list, start_day, duration_days, 
                                     report_description, nodeset_config, type)
        self.max_number_reports = max_number_reports
        self.reporting_interval = reporting_interval

    def to_dict(self):
        d = super(BaseEventReportIntervalOutput, self).to_dict()
        d["Max_Number_Reports"] = self.max_number_reports
        d["Reporting_Interval"] = self.reporting_interval
        return d


def add_node_demographics_report(cb, stratify_by_gender=0, age_bins=[], IP_key_to_collect=''):
    node_demographics_report = BaseDemographicsReport(stratify_by_gender=stratify_by_gender,
                                                      age_bins=age_bins,
                                                      IP_key_to_collect=IP_key_to_collect,
                                                      type='ReportNodeDemographics')
    cb.add_reports(node_demographics_report)