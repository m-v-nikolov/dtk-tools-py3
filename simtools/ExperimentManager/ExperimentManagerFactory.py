import os
from simtools.SetupParser import SetupParser
from simtools.Utilities.General import init_logging

logger = init_logging('ExperimentManager')


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
    def from_experiment(cls, experiment, generic=False):
        logger.debug("Factory - Creating ExperimentManager for experiment %s pid: %d location: %s" % (experiment.id, os.getpid(), experiment.location))
        manager_class = cls.factory(type=experiment.location)
        if generic: # ask the manager class for the location. USE ONLY FROM Overseer, who doesn't know better.
            try:
                orig_block = SetupParser.selected_block
                SetupParser.override_block(manager_class.location) # manager class constructor MAY access SetupParser
                manager = manager_class('', experiment)
            finally:
                SetupParser.override_block(orig_block)
        else:
            manager = manager_class('', experiment)
        return manager

    @classmethod
    def from_model(cls, model_file, location='LOCAL'):
        logger.debug('Factory - Initializing %s ExperimentManager from: %s', location, model_file)
        return cls.factory(location)(model_file, None)

    @classmethod
    def from_setup(cls):
        location = SetupParser.get('type')
        logger.debug('Factory - Initializing %s ExperimentManager from parsed setup' % location)
        return cls.factory(location)(SetupParser.get('exe_path'), None)