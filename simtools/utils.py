import cStringIO
import contextlib
import os
import re
import shutil
import sys
from hashlib import md5

from COMPS import Client

max_exp_name_len = 100
logging_initialized = False
def init_logging(name):
    import logging
    import logging.config
    global logging_initialized

    if not logging_initialized:
        current_dir = os.path.dirname(os.path.realpath(__file__))
        logging.config.fileConfig(os.path.join(current_dir, 'logging.ini'), disable_existing_loggers=False)
        logging_initialized = True
    return logging.getLogger(name)

logger = init_logging('Utils')

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
    # logger.propagate = False
    # previous_level = logging.root.manager.disable
    # logging.disable(logging.CRITICAL)

    yield

    # Restore
    if not stdout:
        sys.stdout = save_stdout
    if not stderr:
        sys.stderr = save_stderr

    # logger.propagate = True
    # logging.disable(previous_level)


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


def COMPS_login(endpoint):
    from COMPS import Client
    #with nostdout():
    try:
        am= Client.auth_manager()
    except:
        Client.Login(endpoint)

    return Client


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


path_translations = {}
def translate_COMPS_path(path, setup=None):
    """
    Transform a COMPS path into fully qualified path.
    Supports:
    - $COMPS_PATH('BIN')
    - $COMPS_PATH('USER')
    - $COMPS_PATH('PUBLIC')
    - $COMPS_PATH('INPUT')
    - $COMPS_PATH('HOME')

    Query the COMPS Java client with the current environment to get the correct path.
    :param path: The COMPS path to transform
    :param setup: The setup to find user and environment
    :return: The absolute path
    """
    # Create the regexp
    regexp = re.search('.*(\$COMPS_PATH\((\w+)\)).*', path)

    # If no COMPS variable found -> return the path untouched
    if not regexp:
        return path

    # Check if we have a setup
    if not setup:
        from simtools.SetupParser import SetupParser
        setup = SetupParser()

    # Retrieve the variable to translate
    groups = regexp.groups()
    comps_variable = groups[1]

    # Is the path already cached
    if comps_variable in path_translations:
        abs_path = path_translations[comps_variable]
    else:
        # Prepare the variables we will need
        environment = setup.get('environment')

        #Q uery COMPS to get the path corresponding to the variable
        COMPS_login(setup.get('server_endpoint'))
        abs_path = Client.auth_manager().get_environment_macros(environment)[groups[1]]

        # Cache
        path_translations[comps_variable] = abs_path

    # Replace and return
    user = setup.get('user')
    return path.replace(groups[0], abs_path).replace("$(User)", user)


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


def stage_file(from_path, to_directory):
    if is_remote_path(from_path):
        logger.info('File is already staged; skipping copy to file-share')
        return from_path

    # Translate $COMPS path if needed
    to_directory_translated = translate_COMPS_path(to_directory)

    file_hash = get_md5(from_path)
    logger.info('MD5 of ' + os.path.basename(from_path) + ': ' + file_hash)

    # We need to use the translated path for the copy but return the untouched staged path
    stage_dir = os.path.join(to_directory_translated, file_hash)
    stage_path = os.path.join(stage_dir, os.path.basename(from_path))
    original_stage_path = os.path.join(to_directory,file_hash,os.path.basename(from_path))

    if not os.path.exists(stage_dir):
        try:
            os.makedirs(stage_dir)
        except:
            raise Exception("Unable to create directory: " + stage_dir)

    if not os.path.exists(stage_path):
        logger.info('Copying %s to %s (translated in: %s)' % (os.path.basename(from_path), to_directory, to_directory_translated))
        shutil.copy(from_path, stage_path)
        logger.info('Copying complete.')

    return original_stage_path


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


def validate_exp_name(exp_name):
    if len(exp_name) > max_exp_name_len:
        logger.info(
            "The experiment name '%s' exceeds the max length %s, please adjust your experiment name. Exiting...",
            exp_name, max_exp_name_len)
        return False
    else:
        return True


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


