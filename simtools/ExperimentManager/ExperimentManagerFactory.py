import json

from simtools import utils
import logging

from simtools.SetupParser import SetupParser

logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


class ExperimentManagerFactory(object):
    @staticmethod
    def factory(type):
        if type == 'LOCAL':
            from simtools.ExperimentManager.LocalExperimentManager import LocalExperimentManager
            return LocalExperimentManager
        if type == 'HPC':
            from simtools.ExperimentManager.CompsExperimentManager import CompsExperimentManager
            return CompsExperimentManager
        raise Exception("ExperimentManagerFactory location argument should be either 'LOCAL' or 'HPC'.")

    @classmethod
    def from_model(cls, model_file, location='LOCAL', setup=None, **kwargs):
        logger.info('Initializing %s ExperimentManager from: %s', location, model_file)
        if not setup:
            setup = SetupParser()
        if location == 'HPC' and kwargs:
            utils.override_HPC_settings(setup, **kwargs)
        return cls.factory(location)(model_file, {}, setup)

    @classmethod
    def from_setup(cls, setup=None, location='LOCAL', **kwargs):
        if not setup:
            setup = SetupParser()
        logger.info('Initializing %s ExperimentManager from parsed setup', location)
        if location == 'HPC' and kwargs:
            utils.override_HPC_settings(setup, **kwargs)
        return cls.factory(location)(setup.get('exe_path'), {}, setup)

    @classmethod
    def from_data(cls, exp_data):
        logger.info('Reloading ExperimentManager from experiment data')
        return cls.factory(exp_data['location'])('', exp_data)

    @classmethod
    def from_file(cls, exp_data_path, suppress_logging=False, force_block=False):
        if not suppress_logging:
            logger.info('Reloading ExperimentManager from: %s', exp_data_path)
        with open(exp_data_path) as exp_data_file:
            exp_data = json.loads(exp_data_file.read())

        if force_block:
            SetupParser.selected_block = SetupParser.setup_file = None

        return cls.factory(exp_data['location'])('', exp_data)