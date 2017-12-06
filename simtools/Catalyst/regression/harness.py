# currently just copied in from cases/harness.py ; not properly functional
from simtools.SetupParser import SetupParser
from argparse import Namespace
import os
import shutil
import sys
from pprint import pprint
import dtk.commands as commands
import simtools.Utilities.Initialization as init
from subprocess import call
debug = False
SCRIPT_FILENAME = 'catalyst_script.py'
INI_FILENAME = 'simtools.ini'
RUN_BLOCK = 'CATALYSTREGRESSIONHPC'
FLAGS_WITH_NO_ARGS = [
    'raw_data',
    'quiet',
]
FLAGS = {
    # 'config_name': None,
    'sweep_type': '--sweep_type',
    'sweep_method': '--sweep_method',
    'report_type': '--report',
    'report_label': '--report_label',
    'step_from': '--start_step',
    'step_to': '--end_step',
    'experiment_id': '--id',
    'raw_data': '--raw_data',
    'quiet': '--quiet',
}

def construct_call(infix_args, args):
    print('%s %s' % (infix_args, args))
    for k,v in args.items():
        if k in FLAGS_WITH_NO_ARGS:
            if v:
                infix_args.append(FLAGS[k])
        else:
            if not v:
                continue
            infix_args.append(FLAGS[k])
            infix_args.append(v)
    # print('command_line items: %s' % infix_args)
    command_line = ' '.join(infix_args)
    return command_line


# ck4, currently does no discovery; point this to a dir containing a config.json file for now.
def discover_case_directories(root):
    return [root]

    # root = os.path.abspath(root)
    # skip = ['79_STI_GH564_DepositContagion', '77_STI_GH521_RelMgr', '10_STI_Transitory_Hi_Formation_Rate',
    #         '11_STI_Transitory_Concurrent', '12_STI_Transitory_Concurrent_JustMales', '101_MaleCircumcision',
    #         '102_STIBarrier', '13_STI_Marital_Only_No_Disease', '14_STI_Informal_Only_No_Disease'] # ck4
    # listing = os.listdir(root)
    # cases = [os.path.join(root, d) for d in listing if os.path.isdir(os.path.join(root, d)) and d not in skip]
    # from pprint import pprint
    # pprint(sorted(cases))
    # return cases



##########################################################################################################

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(dest='regression_root_directory',
                        help='Name of directory in which to find regressions to run.')
    parser.add_argument('-s', '--sweep_type', dest='sweep_type', required=True,
                                 choices=['timestep', 'popscaling'],
                                 help='The type of performance sweep to run and report on.')
    parser.add_argument('-m', '--sweep_method', dest='sweep_method', type=str, default=None,
                                 help='The sweeping method to use (depends on sweep_type).')
    parser.add_argument('-r', '--report', dest='report_type', type=str, default=None,
                                 help='The type of report to generate.')
    parser.add_argument('-id', '--id', dest='experiment_id', default=None,
                                 help='Experiment ID to generate a report for. No new simulations are run if provided.')
    parser.add_argument('--start_step', default=None, type=int, dest='step_from',
                                 help="Starting time step for analysis.")
    parser.add_argument('--end_step', default=None, type=int, dest='step_to',
                                 help="Ending time step for analysis.")
    parser.add_argument('--raw_data', default=False, action='store_true',
                                 help="Saves raw simulation data into a raw_data.csv file. This option may noticeably increase the report generation time.")
    parser.add_argument('-l', '--report_label', default=None, type=str,
                                 help='Additional descriptive label to attach to reporting directory (Default: None)')
    args = parser.parse_args()
    # print(args)
    # exit()

    original_directory = os.getcwd()

    regression_root_directory = args.regression_root_directory # sys.argv[1] # dtk-trunk/Regression
    # report_type = args.report_type # sys.argv[2]

    # regression_input_directory = sys.argv[2] # EMOD-InputData
    script_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), SCRIPT_FILENAME)
    ini_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), INI_FILENAME)

    regression_case_directories = discover_case_directories(regression_root_directory)

    for case_directory in regression_case_directories:
        # try:
        os.chdir(case_directory)
        # print('MOVED TO: %s' % os.getcwd())
        shutil.copyfile(script_filename, SCRIPT_FILENAME)
        shutil.copyfile(ini_filename, INI_FILENAME)

        # ck4, warning! hardcoded values used for now here!
        arguments = {
            # 'config_name': os.path.join(os.getcwd(), SCRIPT_FILENAME),
            'sweep_type': args.sweep_type, #'timestep', #'popscaling',
            'sweep_method': args.sweep_method, #'timestep', #''fixed',
            'report_type': args.report_type, # 'HIV',
            'raw_data': True,
            'report_label': 'timestep-timestep-generic', #'popscaling-fixed-generic',
            'quiet': False,
            # 'block': RUN_BLOCK, # ck4, put in infix_args
            # 'step_from': None,
            # 'step_to': None,
            # 'experiment_id': None # None #'3d7d5353-d6d4-e711-940a-0050569e0ef3' # 'ddbf0521-b8d4-e711-940a-0050569e0ef3' #None #'0bfa7332-c7cf-e711-940a-0050569e0ef3' # '0bfa7332-c7cf-e711-940a-0050569e0ef3' # None # 'c0e134d2-bfcf-e711-940a-0050569e0ef3' # None #'b6fb7a20-b6cf-e711-940a-0050569e0ef3' # ck4, temporary
        }
        if args.step_from:
            arguments['step_from'] = args.step_from
        if args.step_to:
            arguments['step_to'] = args.step_to
        if args.experiment_id:
            arguments['experiment_id'] = args.experiment_id

        # ck4, non-programmatic route
        config_name = SCRIPT_FILENAME # os.path.join(os.getcwd(), SCRIPT_FILENAME)
        infix_args = ['dtk', 'catalyst', config_name, '--%s'%RUN_BLOCK]
        command_line = construct_call(infix_args, arguments)
        print(command_line)
        # continue
        with open('catalyst_command.txt','w') as f:
            f.write(command_line)
        failed = call(command_line)
        os.chdir(original_directory)
        if failed:
            message = 'Case failed: %s\n' % case_directory
        else:
            message = 'Case succeeded: %s\n' % case_directory
        with open('harness.log', 'a') as f:
            f.write(message)

        # ck4, programmatic route
        # # Catalyst-catalyst-speedup-test-Catalyst-regression-development-popscaling-fixed-generic_0bfa7332-c7cf-e711-940a-0050569e0ef3
        # pprint('arguments: %s' % arguments)
        # args = Namespace()
        # for k,v in arguments.items():
        #     setattr(args, k, v)
        # unknownArgs = []
        #
        # # This is it! This is where SetupParser gets set once and for all. Until you run 'dtk COMMAND' again, that is.
        # print('CURRENTLY IN DIR: %s' % os.getcwd())
        # init.initialize_SetupParser_from_args(args, unknownArgs)
        # commands.catalyst(args, unknownArgs)
    # except Exception as e:
        #     print('caught exception!!!')
        #     print('exception type: %s' % type(e))
        #     os.chdir(original_directory)
        #     with open('harness.log', 'a') as f:
        #         f.write('Case failed: %s %s:%s\n' % (case_directory, type(e), str(e)))
        #     print(type(e))
        #     raise e
        # else:
        #     print('** No exceptions, continuing')
        #     os.chdir(original_directory)
        #     with open('harness.log', 'a') as f:
        #         f.write('Case succeeded: %s\n' % case_directory)
        # finally:
        #     SetupParser._uninit() # to allow normal running of next pass

if __name__ == '__main__':
    from multiprocessing import freeze_support
    freeze_support()
    main()

