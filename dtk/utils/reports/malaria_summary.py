from dtk.utils.reports.MalariaReport import MalariaReport

def add_summary_report(cb, start=0, interval=365, nreports=10000, 
                       description = 'AnnualAverage', 
                       age_bins = [ 1.0/12, 0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20, 25, 30, 40,  50,  60, 1000 ]):

    summary_report = MalariaReport(event_trigger_list=['EveryUpdate'],
                                   start_day = start,
                                   report_description = description,
                                   age_bins =  age_bins,
                                   max_number_reports = nreports,
                                   reporting_interval = interval,
                                   type = "MalariaSummaryReport" )

    # TODO: we may want to just return the report or bucket
    #       in case we want to merge with other reporters into the same builder

    # TODO: we may also want to be explicit about what DLL needs to be loaded here

    return summary_report
