import os
import sys
from importlib import import_module

from simtools.SetupParser import SetupParser
from simtools.Utilities.General import init_logging
logger = init_logging('Initialization')

def load_config_module(config_name):
    # Support of relative paths
    config_name = config_name.replace('\\', '/')
    if '/' in config_name:
        splitted = config_name.split('/')[:-1]
        sys.path.append(os.path.join(os.getcwd(), *splitted))
    else:
        sys.path.append(os.getcwd())

    module_name = os.path.splitext(os.path.basename(config_name))[0]

    try:
        return import_module(module_name)
    except ImportError as e:
        e.args = ("'%s' during loading module '%s' in %s files: %s." %
              (e.message, module_name, os.getcwd(), os.listdir(os.getcwd())),)
        raise e

def initialize_SetupParser_from_args(args, unknownArgs):
    # determine the selected environment
    if hasattr(args, 'block'):
        selected_block = args.block # we should use this going forward (add flags in commands_args.py)
    else:
        # current, back-compatible route. This should go away once ini block selection is done via a known flag
        # in all commands
        if len(unknownArgs) == 1:
            import re
            arg = unknownArgs[0]
            block_regex = re.compile('^--(?P<block>\w+)$')
            if block_regex.search(arg):
                selected_block = block_regex.search(arg).group('block')
            else:
                selected_block = None # we use the default block selection in SetupParser
        elif len(unknownArgs) > 1:
            raise Exception("Only zero or one unknown args are allowed for simtools.ini block selection.")
        else: # len(unknownArgs) == 0, use SetupParser default block selection
            selected_block = None

    # some HPC environment overrides that may have been provided on the command line
    overrides = grab_HPC_overrides(args)

    #if hasattr(args, 'ini'):
    #    provided_ini = args.ini
    #else:
    #    provided_ini = None

    # If a config module (experiment .py file) was provided, it MAY have set some SetupParser defaults, so we load
    # it first.
    load_config(args)
    SetupParser.init(selected_block=selected_block, overrides=overrides)

def load_config(args):
    if hasattr(args, 'config_name'):
        # dtk commands (like run) that use such modules should use args.loaded_module and NOT reload the module
        args.loaded_module = load_config_module(args.config_name)
        delattr(args, 'config_name')

def grab_HPC_overrides(args):
    """
    Removes specific known HPC command-line overrides from the provided args object and returns them
    as dict key/value pairs. These overrides can then be passed to SetupParser.init() for its one-and-only
    initialization.
    :param args: an parsed arg object
    :return: a dict of override key/value pairs provided on the command line
    """
    valid_values = dict(priority=['Lowest', 'BelowNormal', 'Normal', 'AboveNormal', 'Highest'],
                        node_group=['emod_32cores', 'emod_a', 'emod_b', 'emod_c', 'emod_d', 'emod_ab', 'emod_cd',
                                    'emod_abcd'],
                        use_comps_asset_svc=['0', '1'])

    overrides = {}
    for parameter in valid_values.keys():
        if hasattr(args, parameter):
            override_value = getattr(args, parameter)
            if override_value is None:
                continue
            if override_value in valid_values[parameter]:
                logger.info('Overriding HPC parameter %s: %s', parameter, override_value)
                overrides[parameter] = override_value
                delattr(args, parameter)
            else:
                logger.warning('Trying to override HPC parameter with unknown value, %s: %s', parameter, override_value)
    return overrides