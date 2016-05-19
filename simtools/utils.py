import os
import glob
from hashlib import md5
import logging
import shutil

logger = logging.getLogger(__name__)

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

def exp_files(idOrName = None):
    files = None

    if idOrName:
        files = glob.glob('simulations/*' + idOrName + '*.json')
    else:
        files = glob.glob('simulations/*.json')

    if not files or len(files) < 1:
        raise Exception('Unable to find experiment meta-data file in local directory.')

    return files

def exp_file(idOrName = None):
    return max(exp_files(idOrName), key=os.path.getctime)

def is_remote_path(path):
    return path.startswith('\\\\')

def stage_file(from_path, to_directory):
    if is_remote_path(from_path):
        logger.info('File is already staged; skipping copy to file-share')
        return from_path

    file_hash = get_md5(from_path)
    logger.info('MD5 of ' + os.path.basename(from_path) + ': ' + file_hash)

    stage_dir = os.path.join(to_directory, file_hash)
    stage_path = os.path.join(stage_dir, os.path.basename(from_path))

    if not os.path.exists(stage_dir):
        try:
            os.makedirs(stage_dir)
        except:
            raise Exception("Unable to create directory: " + stage_dir)

    if not os.path.exists(stage_path):
        logger.info('Copying ' + os.path.basename(from_path) + ' to ' + to_directory + '...')
        shutil.copy(from_path, stage_path)
        logger.info('Copying complete.')

    return stage_path


def override_HPC_settings(setup, **kwargs):

    overrides_by_variable = dict(priority=['Lowest', 'Below Normal', 'Normal', 'Above Normal', 'Highest'],
                                 node_group=['emod_32cores', 'emod_a', 'emod_b', 'emod_c', 'emod_d', 'emod_ab', 'emod_cd', 'emod_abcd'],
                                 use_comps_asset_svc=['0', '1'])

    for variable, allowed_overrides in overrides_by_variable.items():
        value = kwargs.get(variable)
        if value:
            if value in allowed_overrides:
                logger.info('Overriding HPC %s: %s', variable, value)
                setup.set('HPC', variable, value)
            else:
                logger.warning('Trying to override HPC setting with unknown %s: %s', variable, value)


class CommandlineGenerator(object):
    '''
    A class to construct command line strings from executable, options, and params
    '''

    def __init__(self, exe_path, options, params):
        self._exe_path = exe_path
        self._options  = options
        self._params   = params

    @property
    def Executable(self):
        return self._exe_path

    @property
    def Options(self):
        options = []
        for k, v in self._options.items():
            if k[-1] == ':':
                options.append(k + v)   # if the option ends in ':', don't insert a space
            else:
                options.extend([k, v])   # otherwise let join (below) add a space

        return ' '.join(options)

    @property
    def Params(self):
        return ' '.join(self._params)

    @property
    def Commandline(self):
        return ' '.join(filter(None, [self.Executable, self.Options, self.Params]))  # join ignores empty strings
