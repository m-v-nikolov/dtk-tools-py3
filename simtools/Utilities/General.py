import cStringIO
import contextlib
import functools
import logging
import os
import sys

import time

logging_initialized = False
def init_logging(name):
    import logging.config
    global logging_initialized

    if not logging_initialized:
        current_dir = os.path.dirname(os.path.realpath(__file__))
        logging.config.fileConfig(os.path.join(current_dir, 'logging.ini'), disable_existing_loggers=False)
        logging_initialized = True
    return logging.getLogger(name)

try:
    logger = init_logging('Utils')
except:
    pass


def retrieve_item(itemid):
    """
    Return the object identified by id.
    Can be an experiment, a suite or a batch.
    If it is a suite, all experiments with this suite_id will be returned.
    """
    # First try to get an experiment
    from simtools.Utilities.Experiments import retrieve_experiment
    from simtools.DataAccess.DataStore import DataStore
    from simtools.Utilities.COMPSUtilities import exps_for_suite_id
    try:
        return retrieve_experiment(itemid)
    except: pass

    # This was not an experiment, maybe a batch ?
    batch = DataStore.get_batch_by_id(itemid)
    if batch: return batch

    batch = DataStore.get_batch_by_name(itemid)
    if batch: return batch

    # Still no item found -> test the suites
    exps = DataStore.get_experiments_by_suite(itemid)
    if exps: return exps

    # Still not -> last chance is a COMPS suite
    exps = exps_for_suite_id(itemid)
    if exps: return [retrieve_experiment(str(exp.id)) for exp in exps]

    # Didnt find anything sorry
    raise(Exception('Could not find any item corresponding to %s' % itemid))


def get_os():
    """
    Retrieve OS
    """
    msg = "simtools.Utilities.General.get_os() is deprecated. Use simtools.Utilities.General.LocalOS.name"
    logger.warning(msg)
    print msg

    from simtools.Utilities.LocalOS import LocalOS
    return LocalOS.name


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


def retry_function(func, wait=1.5, max_retries=5):
    """
    Decorator allowing to retry the call to a function with some time in between.
    Usage: 
        @retry_function
        def my_func():
            pass
            
        @retry_function(max_retries=10, wait=2)
        def my_func():
            pass
            
    :param func: 
    :param time_between_tries: 
    :param max_retries: 
    :return: 
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        retExc = None
        for i in xrange(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception, e:
                retExc = e
                time.sleep(wait)
        raise retExc
    return wrapper


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
    from hashlib import md5
    import uuid
    logger.info('Getting md5 for ' + filename)

    if not os.path.exists(filename):
        logger.error("The file %s does not exist ! No MD5 could be computed..." % filename)
        return None

    with open(filename, 'rb') as f:
        md5calc = md5()
        while True:
            data = f.read(int(1e8))
            if len(data) == 0: break
            md5calc.update(data)

    return uuid.UUID(md5calc.hexdigest())


def is_remote_path(path):
    return path.startswith('\\\\')


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


def rmtree_f(dir):
    import shutil
    if os.path.exists(dir):
        shutil.rmtree(dir, onerror=rmtree_f_on_error)


def rmtree_f_on_error(func, path, exc_info):
    """
    Error handler for ``shutil.rmtree``.

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.

    Usage : ``shutil.rmtree(path, onerror=onerror)``
    """
    import stat
    if not os.access(path, os.W_OK):
        # Is the error an access error ?
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise


def is_running(pid, name_part):
    """
    Determines if the given pid is running and is running the specified process (name).
    :param pid: The pid to check.
    :param name_part: a case-sensitive partial name by which the thread can be properly identified.
    :return: True/False
    """
    import psutil
    # ck4, This should be refactored to use a common module containing a dict of Process objects
    #      This way, we don't need to do the name() checking, just use the method process.is_running(),
    #      since this method checks for pid number being active AND pid start time.
    if not pid:
        logger.debug("is_running: no valid pid provided.")
        return False

    pid = int(pid)

    try:
        process = psutil.Process(pid)
    except psutil.NoSuchProcess:
        logger.debug("is_running: No such process with pid: %d" % pid)
        return False

    running = process.is_running()
    process_name = process.name()
    valid_name = name_part in process_name

    logger.debug("is_running: pid %s running? %s valid_name (%s)? %s. name: %s" %
                 (pid, running, name_part, valid_name, process_name))

    if is_running and valid_name:
        logger.debug("is_running: pid %s is running and process name is valid." % pid)
        return True

    return False

import importlib
import pkgutil
def import_submodules(package, recursive=True):
    """ Import all submodules of a module, recursively, including subpackages

    :param package: package (name or actual module)
    :type package: str | module
    :rtype: dict[str, types.ModuleType]
    """
    if isinstance(package, str):
        package = importlib.import_module(package)
    results = {}
    for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
        full_name = package.__name__ + '.' + name
        results[full_name] = importlib.import_module(full_name)
        if recursive and is_pkg:
            results.update(import_submodules(full_name))
    return results

labels = [
    (1024 ** 5, ' PB'),
    (1024 ** 4, ' TB'),
    (1024 ** 3, ' GB'),
    (1024 ** 2, ' MB'),
    (1024 ** 1, ' KB'),
    (1024 ** 0, (' byte', ' bytes')),
    ]

verbose = [
    (1024 ** 5, (' petabyte', ' petabytes')),
    (1024 ** 4, (' terabyte', ' terabytes')),
    (1024 ** 3, (' gigabyte', ' gigabytes')),
    (1024 ** 2, (' megabyte', ' megabytes')),
    (1024 ** 1, (' kilobyte', ' kilobytes')),
    (1024 ** 0, (' byte', ' bytes')),
    ]

def file_size(bytes, system=labels):
    """
    Human-readable file size.

    """
    for factor, suffix in system:
        if bytes >= factor:
            break
    amount = int(bytes/factor)
    if isinstance(suffix, tuple):
        singular, multiple = suffix
        if amount == 1:
            suffix = singular
        else:
            suffix = multiple
    return str(amount) + suffix

def trim_leading_file_path(file_path, call_depth=1):
    """
    Removes the leading (left/top-most) path component of the provided file_path
    :param file_path: the file path to remote a compenet from
    :param call_depth: internally used param only; used for correct return when original file_path has only 1 component
    :return: the reconstructed leading-component trimmed file path
    """
    fp, part = os.path.split(file_path)
    if len(fp) == 0: # no leading file path components
        if call_depth == 1: # first pass, keep the one component
            return file_path
        else:
            return '' # ignore last part
    else:
        reconstructed_path = trim_leading_file_path(fp, call_depth=call_depth+1)
        return os.path.join(reconstructed_path, part)

def files_in_dir(dir, filters=None):
    """
    Discovers and returns all files in the provided directory matching the provided glob filters. Returned
    paths are relative to the provided directory.
    :param dir: Find files relative to here
    :return: All files discovered as paths relative to dir
    """
    import fnmatch
    import os

    filters = filters or ['*']
    discovered_files = []
    for root, dirnames, filenames in os.walk(dir):
        for filter in filters:
            for filename in fnmatch.filter(filenames, filter):
                trimmed_root = trim_leading_file_path(root)
                discovered_files.append(os.path.join(trimmed_root, filename))
    return discovered_files

def timestamp_filename(filename, time=None):
    """
    Create a timestamped filename by appending the time to the given filename.
    :param filename: any filename to form the prefix of the output filename
    :return: a filename that is the given filename + a timestamp
    """
    import datetime
    if not time:
        time = datetime.datetime.utcnow()
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    new_filename = '.'.join([filename, timestamp])
    return new_filename

def copy_and_reset_StringIO(sio):
    """
    A method to copy a StringIO and make sure read access starts at the beginning.
    :param sio: A StringIO object
    :return: a copy of sio with read index set to 0
    """
    import copy
    new_sio = copy.deepcopy(sio)
    new_sio.seek(0) # just in case the original had been read some
    return new_sio