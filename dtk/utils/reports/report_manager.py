from dtk.utils.reports.malaria_summary import add_summary_report
from dtk.utils.reports.malaria_survey import add_survey_report
from dtk.utils.reports.malaria_immunity import add_immunity_report
from dtk.utils.reports.CustomReportsBuilder import CustomReportsBuilder
from dtk.utils.reports.CustomReportsBucket import CustomReportsBucket
import os

def add_reports(cb, dll_root, reports={}) :

    report_builder=CustomReportsBuilder()
    dlls = []

    report_types = { 'MalariaSummaryReport' : [],
                    'MalariaImmunityReport' : [],
                    'MalariaSurveyJSONAnalyzer' : [],
                    'MalariaPatientJSONReport' : []}

    for reporter in reports :
        if 'MalariaSummaryReport' in reporter :
            report_types['MalariaSummaryReport'].append(reporter)
        if 'MalariaImmunityReport' in reporter :
            report_types['MalariaImmunityReport'].append(reporter)
        if 'MalariaSurveyJSONAnalyzer' in reporter :
            report_types['MalariaSurveyJSONAnalyzer'].append(reporter)
        if 'MalariaPatientJSONReport' in reporter :
            report_types['MalariaPatientJSONReport'].append(reporter)

    for reporter_type in report_types :
        if len(report_types[reporter_type]) < 1 :
            continue
        if reporter_type == 'MalariaSummaryReport' :
            bucket=CustomReportsBucket("MalariaSummaryReport")

            for reporter in report_types[reporter_type] :
                # default values
                start=0
                interval=365
                nreports=10000
                description = 'AnnualAverage'
                age_bins = [ 1.0/12, 0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20, 25, 30, 40,  50,  60, 1000 ]

                try : 
                    settings = reports[reporter]
                    if 'Start Day' in settings :
                        start = settings['Start Day']
                    if 'Reporting Interval' in settings :
                        interval = settings['Reporting Interval']
                    if 'Max Number of Reports' in settings :
                        nreports = settings['Max Number of Reports']
                    if 'Report Description' in settings :
                        description = settings['Report Description']
                    if 'Age Bins' in settings :
                        age_bins = settings['Age Bins']

                except TypeError :
                    pass

                summary_report = add_summary_report(cb, start, interval, nreports, description, age_bins)
                bucket.add_custom_report(summary_report)

            dlls.append(os.path.join(dll_root, 'libmalariasummary_report_plugin.dll'))

        elif reporter_type == 'MalariaSurveyJSONAnalyzer' :
            bucket=CustomReportsBucket("MalariaSurveyJSONAnalyzer")

            for reporter in report_types[reporter_type] :
                #default values
                survey_days=[0]
                reporting_interval=21
                trigger=["EveryUpdate"]
                nreports=1
                include_births=False
                coverage=1

                try : 
                    settings = reports[reporter]
                    if 'Survey Start Days' in settings :
                        survey_days = settings['Survey Start Days']
                    if 'Reporting Duration' in settings :
                        reporting_interval = settings['Reporting Duration']
                    if 'Trigger Events' in settings :
                        trigger = settings['Trigger Events']
                    if 'Include Births' in settings :
                        include_births = settings['Include Births']
                    if 'Survey Coverage' in settings :
                        coverage = settings['Survey Coverage']
                    if 'Number Reports' in settings :
                        nreports = settings['Number Reports']

                except TypeError :
                    pass

                survey_report = add_survey_report(cb, survey_days, reporting_interval, trigger, nreports, include_births, coverage)
                for sr in survey_report :
                    bucket.add_custom_report(sr)

            dlls.append(os.path.join(dll_root, 'libmalariasurveyJSON_analyzer_plugin.dll'))

        elif reporter_type == 'MalariaImmunityReport' :
            bucket=CustomReportsBucket("MalariaImmunityReport")

            for reporter in report_types[reporter_type] :
                #default values
                start=0
                interval=365
                nreports=1
                description = "FinalYearAverage"
                age_bins = [ 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20, 25, 30, 40,  50,  60, 1000 ]

                try :
                    settings = reports[reporter]
                    if 'Start Day' in settings :
                        start = settings['Start Day']
                    if 'Reporting Interval' in settings :
                        interval = settings['Reporting Interval']
                    if 'Max Number of Reports' in settings :
                        nreports = settings['Max Number of Reports']
                    if 'Report Description' in settings :
                        description = settings['Report Description']
                    if 'Age Bins' in settings :
                        age_bins = settings['Age Bins']

                except TypeError :
                    pass

                immunity_report = add_immunity_report(cb, start, interval, nreports, description, age_bins)
                bucket.add_custom_report(immunity_report)

            dlls.append(os.path.join(dll_root, 'libmalariaimmunity_report_plugin.dll'))

        elif reporter_type == 'MalariaPatientJSONReport' :
            dlls.append(os.path.join(dll_root, 'libmalariapatientJSON_report_plugin.dll'))
            continue

        report_builder.add_report_bucket(bucket)

    cb.custom_reports=report_builder.custom_reports_config_DTK()
    return dlls