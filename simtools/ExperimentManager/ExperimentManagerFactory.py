import json

from dtk.utils.ioformat.OutputMessage import OutputMessage
from simtools import utils
import logging
from simtools.DataAccess.DataStore import DataStore
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
    def from_experiment(cls, experiment):
        logger.info("Reloading ExperimentManager from %s" % experiment)
        return cls.factory(type=experiment.location)('', experiment)

    @classmethod
    def from_model(cls, model_file, location='LOCAL', setup=None, **kwargs):
        logger.info('Initializing %s ExperimentManager from: %s', location, model_file)
        if not setup:
            setup = SetupParser()
        if location == 'HPC' and kwargs:
            utils.override_HPC_settings(setup, **kwargs)
        return cls.factory(location)(model_file, None, setup)

    @classmethod
    def from_setup(cls, setup=None, **kwargs):
        if not setup:
            setup = SetupParser()

        location = setup.get('type')
        logger.info('Initializing %s ExperimentManager from parsed setup', location)

        if location == 'HPC' and kwargs:
            utils.override_HPC_settings(setup, **kwargs)
        return cls.factory(location)(setup.get('exe_path'), None, setup)