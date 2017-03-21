# 'dtk run' options
def populate_run_arguments(subparsers):
    parser_run = subparsers.add_parser('run', help='Run one or more simulations configured by run-options.')
    parser_run.add_argument(dest='config_name', default=None, help='Name of configuration python script for custom running of simulation.')
    parser_run.add_argument('--ini', default=None, help='Specify an overlay configuration file (*.ini).')
    parser_run.add_argument('--priority', default=None, help='Specify priority of COMPS simulation (only for HPC).')
    parser_run.add_argument('--node_group', default=None, help='Specify node group of COMPS simulation (only for HPC).')
    parser_run.add_argument('-b', '--blocking', action='store_true', help='Block the thread until the simulations are done.')
    parser_run.add_argument('-q', '--quiet', action='store_true', help='Runs quietly.')
    parser_run.add_argument('-a', '--analyzer', default=None, help='Specify an analyzer name or configuartion to run upon completion (this operation is blocking).')
    return parser_run


# 'dtk status' options
def populate_status_arguments(subparsers):
    parser_status = subparsers.add_parser('status', help='Report status of simulations in experiment specified by ID or name.')
    parser_status.add_argument(dest='expId', default=None, nargs='?', help='Experiment ID or name.')
    parser_status.add_argument('-r', '--repeat', action='store_true', help='Repeat status check until job is done processing.')
    parser_status.add_argument('-a', '--active', action='store_true', help='Get the status of all active experiments (mutually exclusive to all other options).')
    return parser_status


# 'dtk list' options
def populate_list_arguments(subparsers):
    parser_list = subparsers.add_parser('list', help='Report recent 20 list of simulations in experiment.')
    parser_list.add_argument(dest='exp_name', default=None, nargs='?', help='Experiment name.')
    parser_list.add_argument('-n', '--number', help='Get given number recent experiment list', dest='limit')
    return parser_list


# 'dtk kill' options
def populate_kill_arguments(subparsers):
    parser_kill = subparsers.add_parser('kill', help='Kill most recent running experiment specified by ID or name.')
    parser_kill.add_argument(dest='expId', default=None, nargs='?', help=' Experiment ID or name.')
    parser_kill.add_argument('-s', '--simIds', dest='simIds', default=None, nargs='+', help='Process or job IDs of simulations to kill.')
    return parser_kill


# 'dtk exterminate' options
def populate_exterminate_arguments(subparsers):
    parser_exterminate = subparsers.add_parser('exterminate', help='Kill ALL experiments matched by ID or name.')
    parser_exterminate.add_argument(dest='expId', default=None, nargs='?', help=' Experiment ID or name.')
    return parser_exterminate


 # 'dtk delete' options
def populate_delete_arguments(subparsers):
    parser_delete = subparsers.add_parser('delete', help='Delete the most recent experiment (tracking objects only, e.g., local cache) specified by ID or name.')
    parser_delete.add_argument(dest='expId', default=None, nargs='?', help=' Experiment ID or name.')
    parser_delete.add_argument('--hard', action='store_true', help='Additionally delete working directory or server entities for experiment.')
    return parser_delete


# 'dtk clean' options
def populate_clean_arguments(subparsers):
    parser_clean = subparsers.add_parser('clean', help='Hard deletes ALL experiments in {current_dir}\simulations matched by ID or name.')
    parser_clean.add_argument(dest='expId', default=None, nargs='?', help=' Experiment ID or name.')
    return parser_clean


# 'dtk stdout' options
def populate_stdout_arguments(subparsers):
    parser_stdout = subparsers.add_parser('stdout', help='Print stdout from first simulation in selected experiment.')
    parser_stdout.add_argument(dest='expId', default=None, nargs='?', help=' Experiment ID or name.')
    parser_stdout.add_argument('-s', '--simIds', dest='simIds', default=None, nargs='+', help='Process or job IDs of simulations to print.')
    parser_stdout.add_argument('-c', '--comps', action='store_true', help='Use COMPS asset service to read output files (default is direct file access).')
    parser_stdout.add_argument('-e', '--error', action='store_true', help='Print stderr instead of stdout.')
    parser_stdout.add_argument('--failed', action='store_true', help='Get the stdout for the first failed simulation in the selected experiment.')
    parser_stdout.add_argument('--succeeded', action='store_true', help='Get the stdout for the first succeeded simulation in the selected experiment.')
    return parser_stdout


# 'dtk progress' options
def populate_progress_arguments(subparsers):
    parser_progress = subparsers.add_parser('progress', help='Print progress from simulation(s) in experiment.')
    parser_progress.add_argument(dest='expId', default=None, nargs='?', help=' Experiment ID or name.')
    parser_progress.add_argument('-s', '--simIds', dest='simIds', default=None, nargs='+', help='Process or job IDs of simulations to print.')
    parser_progress.add_argument('-c', '--comps', action='store_true', help='Use COMPS asset service to read output files (default is direct file access).')
    return parser_progress


# 'dtk analyze' options
def populate_analyze_arguments(subparsers):
    parser_analyze = subparsers.add_parser('analyze', help='Analyze finished simulations in experiment according to analyzers.')
    parser_analyze.add_argument('-bn', '--batchName', dest='batchName', default=None, nargs='?', help='Use Batch Name for analyze.')
    parser_analyze.add_argument('-i', '--ids', dest='itemids', default=None, nargs='*', help='IDs of the items to analyze (can be suites, batches, experiments)')
    parser_analyze.add_argument('-a', '--config_name', dest='config_name', default=None,  help='Python script or builtin analyzer name for custom analysis of simulations.')
    parser_analyze.add_argument('-f', '--force', action='store_true', help='Force analyzer to run even if jobs are not all finished.')
    return parser_analyze


# 'dtk create_batch' options
def populate_createbatch_arguments(subparsers):
    parser_createbatch = subparsers.add_parser('create_batch',     help='Create a Batch for later use in Analyze.')
    parser_createbatch.add_argument('-bn', '--batchName', dest='batchName', default=None, nargs='?', help='Use Batch Name.')
    parser_createbatch.add_argument('-i', '--ids', dest='itemids', default=None, nargs='*', help='IDs of the items to analyze (can be suites, batches, experiments)')
    return parser_createbatch

