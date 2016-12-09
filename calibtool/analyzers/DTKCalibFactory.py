import importlib

from calibtool.CalibSite import CalibSite

from calibtool.analyzers.PrevalenceByRoundAnalyzer import PrevalenceByRoundAnalyzer
from calibtool.analyzers.PositiveFractionByDistanceAnalyzer import PositiveFractionByDistanceAnalyzer


class DTKCalibFactory(object):

    @staticmethod
    def get_analyzer(name, weight=1):
        if name == 'PrevalenceByRoundAnalyzer':
            return PrevalenceByRoundAnalyzer(name, weight)
        elif name == 'PositiveFractionByDistanceAnalyzer':
            return PositiveFractionByDistanceAnalyzer(name, weight)
        else:
            # Last chance: Try to import the analyzer in the working directory
            try:
                module = __import__(name, fromlist=[name])
                mod= getattr(module, name)
                return mod(name, weight)
            except:
                raise NotImplemented("Cannot import analyzer %s" % name)

    @staticmethod
    def get_site(name, analyzers):
        try:
            mod = importlib.import_module('calibtool.study_sites.site_%s' % name)
            return CalibSite.from_setup_functions(
                       name=name,
                       setup_functions=mod.setup_functions,
                       reference_data=mod.reference_data,
                       analyzers=analyzers,
                       analyzer_setups=mod.analyzers)
        except ImportError:
            try:
                # Try to import the site in the working directory
                mod = importlib.import_module("site_%s" % name)
                return CalibSite.from_setup_functions(
                    name=name,
                    setup_functions=mod.setup_functions,
                    reference_data=mod.reference_data,
                    analyzers=analyzers,
                    analyzer_setups=mod.analyzers)
            except:
                raise NotImplementedError("Don't recognize CalibSite: %s" % name)

