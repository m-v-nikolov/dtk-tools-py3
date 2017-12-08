import argparse
import json
from collections import defaultdict
import numpy as np
import os
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt

from fidelity_html_report import FidelityHTMLReport
from fidelity_report_analyzer import FidelityReportAnalyzer
from fidelity_report_experiment_definition import FidelityReportExperimentDefinition

# TODO: add logger

# Test base classes
from dtk_case import DTKCase
from base_sim_data_analyzer import BaseSimDataAnalyzer, BaseSimDataChannel

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('exp_def_path', help="Path to a .json file containing experiement definition.")
    parser.add_argument('case_dir_path', help="Path to a dir containing config.json and campaign.json. Top 2 dir names are used as an experiment name if case name is omitted.")
    parser.add_argument('-c', '--case_name', default=None, help="Case name is used as a prefix of the experiemtn name. Experiemnt name is then used as a prefix of the report output dir.")
    parser.add_argument('-b', '--build_label', default='', help="Build label added to the case name.")

    parser.add_argument('-m', '--mode', default=None, help="Json node in exp_def_path to be used.")
    parser.add_argument('-s', '--sweep', default=None, help="Json node in exp_def_path to be used.")
    parser.add_argument('-r', '--report', default=None, help="Json node in exp_def_path to be used.")

    parser.add_argument('-n', '--nruns', default=None, type=int, help="")
    parser.add_argument('-d', '--duration', default=None, type=int, help="")

    parser.add_argument('--report_label', default=None, help="Report_label added to the output dir name.")
    parser.add_argument('--step_from', default=None, type=int, help="From step number.")
    parser.add_argument('--step_to', default=None, type=int, help="To step number")
    # TODO: separate from/to for plotting and measures/stats. In other words, ability to plot entire timeseries and only measure specified range.
    parser.add_argument('--rolling_win_size', default=None, type=int, help="Rolling window size to be used when calculating measures.")

    parser.add_argument('--config', default='config.json', help="")
    parser.add_argument('--campaign', default='campaign.json', help="")

    # ck4, these two... need to be kept for test team purposes? For researchers: no, they'll use simtools.ini
    # parser.add_argument('--input', default=None, help="Input dir path. The default is input_root from simtools.ini.")
    # parser.add_argument('--exe', default=None, help="")

    parser.add_argument('-x', '--xid', default=None, help="Experiement ID to analyze. If not specified simulations will run and then analyzed. If 'last' is specified the latest ran experiement is analyzed.")

    # ck4, this arg (env) will go away when fully incorporated into dtk-tools
    parser.add_argument('--env', choices=['local', 'hpc', 'hpcmalaria'], default='hpc', help="Environment to run simulations, local or HPC.")
    parser.add_argument('--priority', default=False, action='store_true' , help="Run with highest priority to measure performance.")
    parser.add_argument('--raw_data', default=False, action='store_true', help="Saves raw simulation data into a raw_data.csv file. This option may noticeably increase the report generation time.")

    parser.add_argument('--out_root', default=None, help="Output dir path. The default is sim_root from simtools.ini.")
    parser.add_argument('--debug', default=False, action='store_true', help="Run debug mode. This will save intermediate dataframes as .csv files.")

    args = None
    args = parser.parse_args()

    exp_id = args.xid
    exp_def = None

    xd_json = None
    with open(args.exp_def_path) as xd_file:
        xd_json = json.load(xd_file)

    if os.path.isfile(args.exp_def_path):
        if exp_id is None and 'exp_id' in xd_json:
            exp_id = xd_json['exp_id']
        else:
            xd_json['exp_id'] = exp_id

        print 'Regenerating report for experiment {}'.format(exp_id)
        # read experiement execution info from exp_def file from the result folder

    # load experiment definition from an existing experiement definition or from an experiment config
    exp_def = FidelityReportExperimentDefinition(xd_json, args)

    print ''
    print 'REPORT DEFINITION:'
    for k in sorted(exp_def.keys()):
        if k.startswith('_'): continue
        print '{}: {}'.format(k, exp_def[k])

    print ''

    sim_duration = None if exp_def['duration'] is None or exp_def['duration'] == 'all' else int(exp_def['duration'])

    import datetime
    start_time = datetime.datetime.now()
    print 'Start time {}'.format(start_time.strftime('%Y%m%d_%H%M%S'))

    current_dir_path = os.getcwd()
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    config_path = args.config
    campaign_path = args.campaign


    config_path = os.path.join(args.case_dir_path, config_path)
    campaign_path = os.path.join(args.case_dir_path, campaign_path)

    sweep = { 'Run_Number': range(1, int(exp_def['nruns']) + 1), exp_def['sweep_param']: exp_def['sweep_values']}

    sim_dir_name1 = os.path.basename(os.path.dirname(args.case_dir_path))
    sim_dir_name2 = os.path.basename(args.case_dir_path)
    case_name_default = '{}-{}'.format(sim_dir_name1, sim_dir_name2)

    # Case name is used as an experiment name. Experiment name is then used as a prefix of the output dir (set in the analyzer).
    case_name = '{}-{}_{}'.format(args.case_name or case_name_default, args.build_label, exp_def['def_name'])
    case_name = case_name.replace('-_', '_')

    c = DTKCase(
        name = case_name,
        out_root_dir_path = args.out_root,
        config_path = config_path,
        campaign_path = campaign_path,
        input_root = None, #args.input,
        env = args.env.upper(),
        exe_path = None, #args.exe,
        spatial_channel_names = exp_def['spatial_channel_names'],
        sim_duration = sim_duration,
        sweep=sweep,
        priority= 'Highest'if args.priority else None
    )

    for k, v in exp_def['init'].iteritems():
        c.set_param(k, v)

    c.analyzers = [
        FidelityReportAnalyzer(
            'output', # os.path.join(c.out_root_dir_path, 'rpt'),
            c.config_name,
            c.campaign_name,
            c.demog_path,
            experiment_definition = exp_def,
            label=args.report_label,
            time_series_step_from=exp_def['step_from'],
            time_series_step_to=exp_def['step_to'],
            time_series_equal_step_count=True,
            raw_data=args.raw_data,
            debug=args.debug)
    ]

    # ck4, these .run() and .analyze() methods are really 'dtk run' and 'dtk analyze' commands thrown together
    # using the 'DTKCase object as a Builder in a way (I think). Can essentially be rewritten into a 'standard'
    # dtk command that directly utilizes the run and analyze commands via commands.py
    # if experiment id is specified onyl analyze that experiment.
    #
    # ck4, actually I am not sure there is a single thing needed from the DTKCase class in the ported version...
    # test team can keep it unmodified, I think and use it for their purposes (I think they use it for other
    # repos, too)
    if exp_id is not None:
        if exp_id == 'last': exp_id = None
        c.analyze(exp_id)
    else:
        c.run()
        c.analyze()

    os.chdir(current_dir_path)

    end_time = datetime.datetime.now()
    print 'End time {}'.format(end_time.strftime('%Y%m%d_%H%M%S'))
    print 'Total run time {}s'.format((end_time - start_time).total_seconds())


if __name__ == "__main__":
    main()