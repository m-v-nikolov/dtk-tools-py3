import unittest

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.utils.reports import *

class TestSummaryReport(unittest.TestCase):

    def setUp(self):
        self.cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')

    def test_summary_report(self):
        add_summary_report(self.cb)
        reportsJSON = format(self.cb.custom_reports)
        self.assertEqual(len(reportsJSON['Custom_Reports']['MalariaSummaryReport']['Reports']), 1)
        self.assertTrue('libmalariasummary_report_plugin.dll' in list(self.cb.dlls)[0])

    def test_immunity_report(self):
        add_immunity_report(self.cb)
        reportsJSON = format(self.cb.custom_reports)
        self.assertEqual(len(reportsJSON['Custom_Reports']['MalariaImmunityReport']['Reports']), 1)
        self.assertTrue('libmalariaimmunity_report_plugin.dll' in list(self.cb.dlls)[0])

    def test_survey_reports(self):
        add_survey_report(self.cb, survey_days=[365, 730])
        reportsJSON = format(self.cb.custom_reports)
        self.assertEqual(len(reportsJSON['Custom_Reports']['MalariaSurveyJSONAnalyzer']['Reports']), 2)
        self.assertTrue('libmalariasurveyJSON_analyzer_plugin.dll' in list(self.cb.dlls)[0])

    def test_multiple_reports(self):
        add_summary_report(self.cb)
        add_immunity_report(self.cb)
        reportsJSON = format(self.cb.custom_reports)
        self.assertEqual(len(reportsJSON['Custom_Reports']['MalariaSummaryReport']['Reports']), 1)
        self.assertEqual(len(reportsJSON['Custom_Reports']['MalariaImmunityReport']['Reports']), 1)
        self.assertTrue(any(['libmalariasummary_report_plugin.dll' in d for d in self.cb.dlls]))
        self.assertTrue(any(['libmalariaimmunity_report_plugin.dll' in d for d in self.cb.dlls]))

if __name__ == '__main__':
    unittest.main()