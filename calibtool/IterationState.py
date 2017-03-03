import json
import logging


import os
import copy
import pandas as pd
import re

from calibtool.utils import ResumePoint
from datetime import datetime
from simtools.Utilities.Encoding import json_numpy_obj_hook, NumpyEncoder

logger = logging.getLogger(__name__)


class IterationState(object):
    '''
    Holds the settings, parameters, simulation state, analysis results, etc.
    for one calibtool iteration.

    Allows for the resumption or extension of existing CalibManager instances
    from an arbitrary point in the iterative process.
    '''

    def __init__(self, **kwargs):
        self.iteration = 0
        self.resume_point = ResumePoint.iteration_start
        self.samples_for_this_iteration = {}
        self.next_point = {}
        self.simulations = {}
        self.experiment_id = None
        self.analyzers = {}
        self.results = {}
        self.working_directory = None

        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def iteration_directory(self):
        return os.path.join(self.working_directory, 'iter%d' % self.iteration)

    def reset_state(self):
        self.samples_for_this_iteration = {}
        self.next_point = {}
        self.simulations = {}
        self.experiment_id = None
        self.analyzers = {}
        self.results = {}

    def reset_to_step(self, iter_step=None):
        last_state_by_step = [('commission', ('samples_for_this_iteration')),
                              ('analyze', ('simulations',)),
                              ('next_point', ('results', 'analyzers'))]

        for step, states in reversed(last_state_by_step):
            if step == iter_step:  # remove cached states back to desired resumption point
                break
            logger.info('Clearing IterationState attribute(s): %s', states)
            for state in states:
                attr = getattr(self, state)
                if isinstance(attr, list):
                    attr[:] = []  # clear() only for dict before Python 3.3
                else:
                    attr.clear()

    def increment_iteration(self):
        self.save()
        self.iteration += 1
        self.reset_state()

    @classmethod
    def from_file(cls, filepath):
        with open(filepath, 'r') as f:
            return cls(**json.load(f, object_hook=json_numpy_obj_hook))

    def to_file(self, filepath):
        # remove resume_point from output
        it_dict = copy.deepcopy(self.__dict__)
        it_dict.pop('resume_point')

        with open(filepath, 'w') as f:
            json.dump(it_dict, f, indent=4, cls=NumpyEncoder)

    @classmethod
    def restore_state(cls, exp_name, iteration):
        """
        Restore IterationState
        """
        iter_directory = os.path.join(exp_name, 'iter%d' % iteration)
        iter_file = os.path.join(iter_directory, 'IterationState.json')
        return cls.from_file(iter_file)

    def set_samples_for_iteration(self, iteration, samples, next_point):
        if isinstance(samples, pd.DataFrame):
            dtypes = {name:str(data.dtype) for name, data in samples.iteritems()}
            self.samples_for_this_iteration_dtypes = dtypes # Argh

            # samples_for_this_iteration[ samples_for_this_iteration.isnull() ] = None # DJK: Is this is necessary on Windows?
            samples_NaN_to_Null = samples.where(~samples.isnull(), other=None)
            self.samples_for_this_iteration = samples_NaN_to_Null.to_dict(orient='list')
        else:
            self.samples_for_this_iteration = samples

        # Also refresh the next point state
        self.set_next_point(next_point)

    # Always trigger a save when setting next_point
    def set_next_point(self, next_point):
        self.next_point = next_point.get_state()
        self.save()

    def save(self, backup_existing=False):
        """
        Cache information about the IterationState that is needed to resume after an interruption.
        If resuming from an existing iteration, also copy to backup the initial cached state.
        """
        try:
            os.makedirs(self.iteration_directory)
        except OSError:
            pass

        iter_state_path = os.path.join(self.iteration_directory, 'IterationState.json')
        if backup_existing and os.path.exists(iter_state_path):
            backup_id = 'backup_' + re.sub('[ :.-]', '_', str(datetime.now().replace(microsecond=0)))
            os.rename(iter_state_path, os.path.join(self.iteration_directory, 'IterationState_%s.json' % backup_id))

        self.to_file(iter_state_path)

