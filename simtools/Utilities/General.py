import cStringIO
import contextlib
import logging
import os
import platform
import sys

from matplotlib.finance import md5


logging_initialized = False
def init_logging(name):
    import logging.config
    global logging_initialized

    if not logging_initialized:
        current_dir = os.path.dirname(os.path.realpath(__file__))
        logging.config.fileConfig(os.path.join(current_dir, 'logging.ini'), disable_existing_loggers=False)
        logging_initialized = True
    return logging.getLogger(name)

logger = init_logging('Utils')

def get_os():
    """
    Retrieve OS
    """
    sy = platform.system()

    # OS: windows
    if sy == 'Windows':
        my_os = 'win'
    # OS: Linux
    elif sy == 'Linux':
        my_os = 'lin'
    # OS: Mac
    else:
        my_os = 'mac'

    return my_os


def utc_to_local(utc_dt):
    import pytz
    from pytz import timezone

    local_tz = timezone('US/Pacific')
    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
    return local_tz.normalize(local_dt) # .normalize might be unnecessary

@contextlib.contextmanager
def nostdout(stdout = False, stderr=False):
    """
    Context used to suppress any print/logging from block of code

    Args:
        stdout: If False, hides. If True Shows. False by default
        stderr: If False, hides. If True Shows. False by default
    """
    # Save current state and disable output
    if not stdout:
        save_stdout = sys.stdout
        sys.stdout  = cStringIO.StringIO()
    if not stderr:
        save_stderr = sys.stderr
        sys.stderr = cStringIO.StringIO()

    # Deactivate logging
    previous_level = logging.root.manager.disable
    logging.disable(logging.ERROR)

    yield

    # Restore
    if not stdout:
        sys.stdout = save_stdout
    if not stderr:
        sys.stderr = save_stderr

    logging.disable(previous_level)


def caller_name(skip=2):
    """
    Get a name of a caller in the format module.class.method

    `skip` specifies how many levels of stack to skip while getting caller
    name. skip=1 means "who calls me", skip=2 "who calls my caller" etc.

    An empty string is returned if skipped levels exceed stack height
    """
    import inspect
    stack = inspect.stack()
    start = 0 + skip
    if len(stack) < start + 1:
      return ''
    parentframe = stack[start][0]

    name = []
    module = inspect.getmodule(parentframe)
    # `modname` can be None when frame is executed directly in console
    if module:
        name.append(module.__name__)
    # detect classname
    if 'self' in parentframe.f_locals:
        name.append(parentframe.f_locals['self'].__class__.__name__)
    codename = parentframe.f_code.co_name
    if codename != '<module>':  # top level usually
        name.append( codename ) # function or a method
    del parentframe
    return ".".join(name)

def remove_null_values(null_dict):
    ret = {}
    for key, value in null_dict.iteritems():
        if value:
            ret[key] = value
    return ret


def get_tools_revision():
    # Get the tools revision
    try:
        import subprocess
        file_dir = os.path.dirname(os.path.abspath(__file__))
        revision = subprocess.check_output(["git", "describe", "--tags"], cwd=file_dir).replace("\n", "")
    except:
        revision = "Unknown"

    return revision

def get_md5(filename):
    logger.info('Getting md5 for ' + filename)
    with open(filename) as file:
        md5calc = md5()
        while True:
            data = file.read(10240)  # value picked from example!
            if len(data) == 0:
                break
            md5calc.update(data)
    md5_value = md5calc.hexdigest()
    return md5_value


def is_remote_path(path):
    return path.startswith('\\\\')



def override_HPC_settings(setup, **kwargs):
    overrides_by_variable = dict(priority=['Lowest', 'BelowNormal', 'Normal', 'AboveNormal', 'Highest'],
                                 node_group=['emod_32cores', 'emod_a', 'emod_b', 'emod_c', 'emod_d', 'emod_ab',
                                             'emod_cd', 'emod_abcd'],
                                 use_comps_asset_svc=['0', '1'])

    for variable, allowed_overrides in overrides_by_variable.items():
        value = kwargs.get(variable)
        if value:
            if value in allowed_overrides:
                logger.info('Overriding HPC %s: %s', variable, value)
                setup.set(variable, value)
            else:
                logger.warning('Trying to override HPC setting with unknown %s: %s', variable, value)


class CommandlineGenerator(object):
    """
    A class to construct command line strings from executable, options, and params
    """

    def __init__(self, exe_path, options, params):
        self._exe_path = exe_path
        self._options = options
        self._params = params

    @property
    def Executable(self):
        return self._exe_path

    @property
    def Options(self):
        options = []
        for k, v in self._options.items():
            # Handles spaces
            value = '"%s"' % v if ' ' in v else v
            if k[-1] == ':':
                options.append(k + value)  # if the option ends in ':', don't insert a space
            else:
                options.extend([k, value])  # otherwise let join (below) add a space

        return ' '.join(options)

    @property
    def Params(self):
        return ' '.join(self._params)

    @property
    def Commandline(self):
        return ' '.join(filter(None, [self.Executable, self.Options, self.Params]))  # join ignores empty strings


