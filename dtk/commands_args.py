import argparse


def populate_run_arguments(subparsers):
    parser_run = subparsers.add_parser('run', help='Run one or more simulations configured by run-options.')
    parser_run.add_argument(dest='config_name', default=None,
                            help='Name of configuration python script for custom running of simulation.')
    parser_run.add_argument('--ini', default=None, help='Specify an overlay configuration file (*.ini).')
    parser_run.add_argument('--priority', default=None, help='Specify priority of COMPS simulation (only for HPC).')
    parser_run.add_argument('--node_group', default=None, help='Specify node group of COMPS simulation (only for HPC).')
    parser_run.add_argument('-b', '--blocking', action='store_true',
                            help='Block the thread until the simulations are done.')
    parser_run.add_argument('-q', '--quiet', action='store_true', help='Runs quietly.')
    parser_run.add_argument('-a', '--analyzer', default=None,
                            help='Specify an analyzer name or configuartion to run upon completion (this operation is blocking).')
    return parser_run


def populate_status_arguments(parser_status):
    parser_status.add_argument(dest='expId', default=None, nargs='?', help='Experiment ID or name.')
    parser_status.add_argument('-r', '--repeat', action='store_true',
                               help='Repeat status check until job is done processing.')
    parser_status.add_argument('-a', '--active', action='store_true',
                               help='Get the status of all active experiments (mutually exclusive to all other options).')
