from PrevalenceAnalyzer import PrevalenceAnalyzer
from calibtool.CalibSite import CalibSite
from calibtool.study_sites.site_setup_functions import  summary_report_fn


class MyanmarCalibSite(CalibSite):

    def get_reference_data(self, reference_type):
        return []

    def __init__(self):
        super(MyanmarCalibSite, self).__init__('Myanmar')

    def get_analyzers(self):
        return [PrevalenceAnalyzer(self)]

    def get_setup_functions(self):
        return [
            summary_report_fn(start=50*365),
            lambda cb: cb.update_params( { 'logLevel_LarvalHabitatMultiplier' : 'WARNING'})
        ]