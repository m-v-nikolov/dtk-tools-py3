import importlib

from calibtool.CalibSite import CalibSite

from calibtool.analyzers.ClinicalIncidenceByAgeCohortAnalyzer import ClinicalIncidenceByAgeCohortAnalyzer


class DTKCalibFactory(object):

    @staticmethod
    def get_analyzer(name, weight=1):
        if name == 'ClinicalIncidenceByAgeCohortAnalyzer':
            return ClinicalIncidenceByAgeCohortAnalyzer(name, weight)
        else:
            raise NotImplementedError("Don't recognize CalibAnalyzer: %s" % name)

    @staticmethod
    def get_site(name, analyzers):
        try:
            mod = importlib.import_module('dtk.calibration.study_sites.site_%s' % name)
            return CalibSite.from_setup_functions(
                       name=name,
                       setup_functions=mod.setup_functions,
                       reference_data=mod.reference_data,
                       analyzers=analyzers)
        except ImportError:
            raise NotImplementedError("Don't recognize CalibSite: %s" % name)

