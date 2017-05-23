import json
import os
import copy
import pandas as pd
import re
from calibtool.utils import ResumePoint
from datetime import datetime
from simtools.SetupParser import SetupParser
from simtools.Utilities.Encoding import json_numpy_obj_hook, NumpyEncoder
from simtools.Utilities.Experiments import retrieve_experiment
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.Utilities.General import init_logging

logger = init_logging("Calibration")


class IterationState(object):
    '''
    Holds the settings, parameters, simulation state, analysis results, etc.
    for one calibtool iteration.

    Allows for the resumption or extension of existing CalibManager instances
    from an arbitrary point in the iterative process.
    '''

    def __init__(self, **kwargs):
        self.iteration = 0
        self.status = ResumePoint.iteration_start
        self.resume_point = ResumePoint.iteration_start
        self.iter_step = 'commission'
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
        it_dict.pop('iter_step')
        it_dict['status'] = it_dict['status'] .name

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

    # resume stuff...
    def prepare_resume_state(self, calibManager, iteration, iter_step):

        self.iteration = iteration
        self.iter_step = iter_step.lower() if iter_step is not None else ''

        if not os.path.isdir(calibManager.name):
            raise Exception('Unable to find existing calibration in directory: %s' % calibManager.name)

        calib_data = calibManager.read_calib_data()
        if calib_data is None or not calib_data:
            raise Exception('Metadata is empty in %s/CalibManager.json' % calibManager.name)

        calibManager.suites = calib_data.get('suites')
        calibManager.latest_iteration = int(calib_data.get('iteration', 0))

        self.find_best_iteration_for_resume(calibManager)
        it = IterationState.restore_state(calibManager.name, self.iteration)
        self.status = ResumePoint[it.status]

        self.prepare_resume_point_for_iteration(calibManager)

        # Restore the results
        if self.resume_point.value < ResumePoint.plot.value:
            # it will combine current results with previous results
            self.restore_results(calibManager, calib_data.get('results'), self.iteration - 1)
        else:
            # it will use the current results and resume from next iteration
            self.restore_results(calibManager, calib_data.get('results'), self.iteration)

        # Make a backup of CalibManager.json
        calibManager.backup_calibration()

    def restore_results(self, calibManager, results, iteration):
        """
        Restore summary results from serialized state.
        """
        if not results:
            logger.debug('No cached results to reload from CalibManager.')
            return

        # Depending on the type of results (lists or dicts), handle differently how we treat the results
        # This should be refactor to take care of both cases at once
        if isinstance(results, dict):
            calibManager.all_results = pd.DataFrame.from_dict(results, orient='columns')
            calibManager.all_results.set_index('sample', inplace=True)
            calibManager.all_results = calibManager.all_results[calibManager.all_results.iteration <= iteration]
        elif isinstance(results, list):
            calibManager.all_results = results[iteration]

        logger.debug(calibManager.all_results)

    def check_leftover(self, calibManager):
        """
            - Handle the case: process got interrupted but it still runs on remote
            - Handle location change case: may resume from commission instead
        """
        # Step 1: Checking possible location changes
        try:
            exp_id = self.experiment_id
            exp = retrieve_experiment(exp_id)
        except:
            exp = None
            import traceback
            traceback.print_exc()

        if not exp:
            var = raw_input("Cannot restore Experiment 'exp_id: %s'. Force to resume from commission... Continue ? [Y/N]" % exp_id if exp_id else 'None')
            # force to resume from commission
            if var.upper() == 'Y':
                self.iter_step = 'commission'
            else:
                logger.info("Answer is '%s'. Exiting...", var.upper())
                exit()

        # If location has been changed, will double check user for a special case before proceed...
        if calibManager.location != exp.location and self.iter_step in ['analyze', 'plot', 'next_point']:
            location = SetupParser.get('type')
            var = raw_input("Location has been changed from '%s' to '%s'. Resume will start from commission instead, do you want to continue? [Y/N]:  " % (exp.location, location))
            if var.upper() == 'Y':
                self.iter_step = 'commission'
            else:
                logger.info("Answer is '%s'. Exiting...", var.upper())
                exit()

        # Save the selected block the user wants
        user_selected_block = SetupParser.selected_block

        # Step 2: Checking possible leftovers
        try:
            # Retrieve the experiment manager. Note: it changed selected_block
            calibManager.exp_manager = ExperimentManagerFactory.from_experiment(exp)
        except Exception:
            logger.info('Proceed without checking the possible leftovers.')
        finally:
            # Restore the selected block
            SetupParser.override_block(user_selected_block)

        if not calibManager.exp_manager: return

        # Don't do the leftover checking for a special case
        if self.iter_step == 'commission':
            return

        # Make sure it is finished
        calibManager.exp_manager.wait_for_finished(verbose=True)

        try:
            # check the status
            states = calibManager.exp_manager.get_simulation_status()[0]
        except:
            # logger.info(ex)
            logger.info('Proceed without checking the possible leftovers.')
            return

        if not states:
            logger.info('Proceed without checking the possible leftovers.')
            return

    def prepare_resume_point_for_iteration(self, calibManager):
        """
        Setup resume point the point to resume the iteration:
           * commission -- commission a new iteration of simulations based on existing next_params
           * analyze -- calculate results for an existing iteration of simulations
           * next_point -- generate next sample points from an existing set of results
        """
        # Restore current iteration and next_point
        self.restore_next_point_for_iteration(calibManager)

        # Check leftover (in case lost connection) and also consider possible location change.
        self.check_leftover(calibManager)

        # Adjust resuming point based on input options
        if self.iter_step:
            self.adjust_resume_point(calibManager)

        # transfer the final resume point
        self.resume_point = self.status

        # Prepare iteration state
        if self.resume_point == ResumePoint.commission:
            # need to run simulations
            self.simulations = {}
            self.results = {}
        elif self.resume_point == ResumePoint.analyze:
            # just need to calculate the results
            self.results = {}
        elif self.resume_point == ResumePoint.plot:
            # just need to do plotting based on the existing results
            pass
        elif self.resume_point == ResumePoint.next_point:
            pass
        else:
            pass

        # adjust next_point
        self.restore_next_point(calibManager)

    def restore_next_point(self, calibManager):
        """
        Restore next_point up to this iteration
        Note: when come to here:
                - self.iteration_state has been restored from current self.iteration already!
                - self.next_point has been restored from current self.iteration already!
        """
        # Handel the general cases for resume
        if self.resume_point == ResumePoint.commission:
            # Note: later will generate new samples. Need to clean up next_point for resume from commission.
            if self.iteration == 0:
                calibManager.next_point.cleanup()
            elif self.iteration > 0:
                # Now we need to restore next_point from previous iteration (need to re-generate new samples late)
                iteration_state = IterationState.restore_state(calibManager.name, self.iteration - 1)
                calibManager.next_point.set_state(iteration_state.next_point, self.iteration - 1)

            # prepare and ready for new experiment and simulations
            self.reset_state()
        elif self.resume_point == ResumePoint.analyze:
            # Note: self.next_point has been already restored from current iteration, so it has current samples!
            if self.iteration == 0:
                calibManager.next_point.cleanup()
            elif self.iteration > 0:
                # Now, we need to restore gaussian from previous iteration
                iteration_state = IterationState.restore_state(calibManager.name, self.iteration - 1)
                calibManager.next_point.restore(iteration_state)
        elif self.resume_point == ResumePoint.plot:
            # Note: self.next_point has been already restored from current iteration, so it has current samples!
            pass
        elif self.resume_point == ResumePoint.next_point:
            # Note: self.next_point has been already restored from current iteration, move on to next iteration!
            pass
        else:
            # in case we have more resuming point in the future
            pass

    def restore_next_point_for_iteration(self, calibManager):
        """
        Restore next_point up to this iteration
        """
        # Restore IterationState and keep the resume_point and iter_step
        it = IterationState.restore_state(calibManager.name, self.iteration)
        for attr, value in it.__dict__.items():
            if attr not in ['iter_step', 'resume_point', 'status']:
                setattr(self, attr, value)

        # Update next point
        calibManager.next_point.set_state(self.next_point, self.iteration)

    def adjust_resume_point(self, calibManager):
        """
        Consider user's input and determine the resuming point
        """
        input_resume_point = ResumePoint[self.iter_step]

        if calibManager.latest_iteration == self.iteration:
            # user input iter_step may not be valid
            if input_resume_point.value <= self.status.value:
                self.status = input_resume_point
            else:
                logger.info("The farthest resume point available is '%s', we will resume from it instead of '%s'" \
                      % (self.status.name, input_resume_point.name))
                answer = raw_input("Would you like to continue ? [Y/N]")
                if answer != "Y":
                    exit()
        else:
            # just take user input iter_step
            self.status = input_resume_point

    def find_best_iteration_for_resume(self, calibManager):
        """
        Find the latest good iteration from where we can do resume
        """
        # If no iteration passed in, take latest_iteration for resume
        if self.iteration is None:
            self.iteration = calibManager.latest_iteration

        # Adjust input iteration
        if calibManager.latest_iteration < self.iteration:
            self.iteration = calibManager.latest_iteration

    def commission_check(self):
        return self.resume_point.value <= ResumePoint.commission.value

    def analyze_check(self):
        return self.resume_point.value <= ResumePoint.analyze.value

    def plotting_check(self):
        return self.resume_point.value <= ResumePoint.plot.value

    def next_point_check(self):
        return self.resume_point.value <= ResumePoint.next_point.value

