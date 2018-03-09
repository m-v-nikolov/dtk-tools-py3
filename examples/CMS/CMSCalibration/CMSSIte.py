from calibtool.CalibSite import CalibSite
from examples.CMS.CMSCalibration.CMSAnalyzer import CMSAnalyzer


class CMSSite(CalibSite):
    def __init__(self):
        super().__init__("CMSSite")

    def get_reference_data(self, reference_type=None):
        return {
            "ratio_SI_10": 1,
            "ratio_SI_100": 5
        }

    def get_analyzers(self):
        return CMSAnalyzer(self.get_reference_data()),

    def get_setup_functions(self):
        return []