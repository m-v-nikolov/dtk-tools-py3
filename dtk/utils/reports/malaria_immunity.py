from dtk.utils.reports.MalariaReport import MalariaReport
from dtk.utils.reports.CustomReportsBucket import CustomReportsBucket
from dtk.utils.reports.CustomReportsBuilder import CustomReportsBuilder

# Test a survey analyzer distribution
def add_immunity_report(cb, start, interval, nreports, 
                       description = "AnnualAverage", 
                       age_bins = [ 1.0/12, 0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20, 25, 30, 40,  50,  60, 1000 ]):

    immunity_report = MalariaReport(event_trigger_list=['EveryUpdate'],
                                   start_day = start,
                                   report_description = description,
                                   age_bins =  age_bins,
                                   max_number_reports = nreports,
                                   reporting_interval = interval,
                                   type = "MalariaImmunityReport" )

    # TODO: we may want to just return the report or bucket
    #       in case we want to merge with other reporters into the same builder

    # TODO: we may also want to be explicit about what DLL needs to be loaded here
    bucket=CustomReportsBucket("MalariaImmunityReport")
    bucket.add_custom_report(immunity_report)
    report_builder=CustomReportsBuilder()
    report_builder.add_report_bucket(bucket)
    cb.custom_reports=report_builder.custom_reports_config_DTK()
