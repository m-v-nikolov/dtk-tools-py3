
# 'calibtool run' options
def populate_run_arguments(subparsers, func):
    parser_run = subparsers.add_parser('run', help='Run a calibration configured by run-options')
    parser_run.add_argument(dest='config_name', default=None, help='Name of configuration python script for custom running of calibration.')
    parser_run.add_argument('--priority', default=None, help='Specify priority of COMPS simulation (only for HPC).')
    parser_run.add_argument('--node_group', default=None, help='Specify node group of COMPS simulation (only for HPC).')

    parser_run.add_argument('-r', '--resample', default=None, type=str,
                            help='Perform a post-optimization resample-and-run process using this specified resampling '
                                 'technique (Default: None)')
    parser_run.add_argument('-a', '--analyzer', default=None, type=str,
                            help='Analyzer for calculating the liklihood of parameter space points used in the '
                                 'resampling process (Required if using -r) (Default: None')
    parser_run.set_defaults(func=func)

# 'calibtool resume' options
def populate_resume_arguments(subparsers, func):
    parser_resume = subparsers.add_parser('resume', help='Resume a calibration configured by resume-options')
    parser_resume.add_argument(dest='config_name', default=None, help='Name of configuration python script for custom running of calibration.')
    parser_resume.add_argument('--iteration', default=None, type=int, help='Resume calibration from iteration number (default is last cached state).')
    parser_resume.add_argument('--iter_step', default=None, help="Resume calibration on specified iteration step ['commission', 'analyze', 'plot', 'next_point'].")
    parser_resume.add_argument('--priority', default=None, help='Specify priority of COMPS simulation (only for HPC).')
    parser_resume.add_argument('--node_group', default=None, help='Specify node group of COMPS simulation (only for HPC).')
    parser_resume.set_defaults(func=func)

# 'calibtool cleanup' options
def populate_cleanup_arguments(subparsers, func):
    parser_cleanup = subparsers.add_parser('cleanup', help='Cleanup a calibration')
    parser_cleanup.add_argument(dest='config_name', default=None,
                               help='Name of configuration python script for custom running of calibration.')
    parser_cleanup.set_defaults(func=func)

# 'calibtool kill' options
def populate_kill_arguments(subparsers, func):
    parser_cleanup = subparsers.add_parser('kill', help='Kill a calibration')
    parser_cleanup.add_argument(dest='config_name', default=None,
                               help='Name of configuration python script.')
    parser_cleanup.set_defaults(func=func)
    