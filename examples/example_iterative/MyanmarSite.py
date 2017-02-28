from calibtool.CalibSite import CalibSite
from calibtool.study_sites.site_setup_functions import config_setup_fn
from examples.example_iterative.PrevalenceAnalyzer import PrevalenceAnalyzer


class MyanmarCalibSite(CalibSite):
    def __init__(self):
        super(MyanmarCalibSite, self).__init__('Myanmar')

    def get_reference_data(self, reference_type):
        return {}

    def get_analyzers(self):
        return [PrevalenceAnalyzer(self)]

    def get_setup_functions(self):
        return []
