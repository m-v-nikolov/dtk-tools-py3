import gc
import pandas as pd
from calibtool.IterationState import IterationState
from calibtool.utils import StatusPoint
from simtools.SetupParser import SetupParser
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.Utilities.General import init_logging

# from calibtool.plotters import SiteDataPlotter
from simtools.Utilities.Experiments import retrieve_experiment


logger = init_logging("Calibration")


class ResumeIterationState(IterationState):
    """
    Holds the settings, parameters, simulation state, analysis results, etc.
    for one calibtool iteration.

    Allows for the resumption or extension of existing CalibManager instances
    from an arbitrary point in the iterative process.
    """

    def __init__(self, **kwargs):
        super(ResumeIterationState, self).__init__(**kwargs)


    ###################################################
    # Resume
    ###################################################
    def resume(self):
        """
         - prepare all kind of stats for resume
         - then still go into the run_iteration loop
        """
        print 'ResumeIteration: resume'
        self.resume_init()
        self.run()

    def resume_init(self):
        """
        prepare the resume environment
        """
        # step 1: Check leftover (in case lost connection) and also consider possible location change.
        if self.resume_point != StatusPoint.commission and self.resume_point != StatusPoint.next_point:
            self.check_leftover()

        # step 2: restore next_point
        self.restore_next_point()

        # step 3: restore Calibration results
        if self.resume_point.value < StatusPoint.plot.value:
            # it will combine current results with previous results
            self.restore_results(self.iteration - 1)
        else:
            # it will use the current results and resume from next iteration
            self.restore_results(self.iteration)

        # step 4: prepare resume states
        if self.resume_point == StatusPoint.commission:
            # need to run simulations
            self.simulations = {}
            self.results = {}
        elif self.resume_point == StatusPoint.analyze:
            # just need to calculate the results
            self.results = {}
        elif self.resume_point == StatusPoint.plot:
            # just need to do plotting based on the existing results
            pass
        elif self.resume_point == StatusPoint.next_point:
            pass
        else:
            pass

    def restore_results(self, iteration):
        """
        Restore summary results from serialized state.
        """
        # Depending on the type of results (lists or dicts), handle differently how we treat the results
        # This should be refactor to take care of both cases at once
        if isinstance(self.all_results, pd.DataFrame):
            self.all_results.set_index('sample', inplace=True)
            self.all_results = self.all_results[self.all_results.iteration <= iteration]
        elif isinstance(self.all_results, list):
            self.all_results = self.all_results[iteration]

    def check_leftover(self):
        """
            - Handle the case: process got interrupted but it still runs on remote
            - Handle location change case: may resume from commission instead
        """
        try:
            exp_id = self.experiment_id
            exp = retrieve_experiment(exp_id)
        except:
            exp = None
            import traceback
            traceback.print_exc()

        # Save the selected block the user wants
        user_selected_block = SetupParser.selected_block

        try:
            # Retrieve the experiment manager. Note: it changed selected_block
            self.exp_manager = ExperimentManagerFactory.from_experiment(exp)
        except Exception:
            logger.info('Proceed without checking the possible leftovers.')
        finally:
            # Restore the selected block
            SetupParser.override_block(user_selected_block)

        if not self.exp_manager:
            return

        # Make sure it is finished
        self.exp_manager.wait_for_finished(verbose=True)

        try:
            # check the status
            states = self.exp_manager.get_simulation_status()[0]
        except:
            # logger.info(ex)
            logger.info('Proceed without checking the possible leftovers.')
            return

        if not states:
            logger.info('Proceed without checking the possible leftovers.')
            return

    def restore_next_point(self):
        """
        Restore next_point up to this iteration
        """
        # initialization and may need adjustment based on resume_point
        self.next_point_algo.set_state(self.next_point, self.iteration)

        # Handel the general cases for resume
        if self.resume_point == StatusPoint.commission:
            # Note: later will generate new samples. Need to clean up next_point for resume from commission.
            if self.iteration == 0:
                self.next_point_algo.cleanup()
            elif self.iteration > 0:
                # Now we need to restore next_point from previous iteration (need to re-generate new samples late)
                iteration_state = IterationState.restore_state(self.calibration_name, self.iteration - 1)
                self.next_point_algo.set_state(iteration_state.next_point, self.iteration - 1)

            # prepare and ready for new experiment and simulations
            self.reset_state()
        elif self.resume_point == StatusPoint.analyze:
            # Note: self.next_point has been already restored from current iteration, so it has current samples!
            if self.iteration == 0:
                self.next_point_algo.cleanup()
            elif self.iteration > 0:
                # Now, we need to restore gaussian from previous iteration
                iteration_state = IterationState.restore_state(self.calibration_name, self.iteration - 1)
                self.next_point_algo.restore(iteration_state)
        elif self.resume_point == StatusPoint.plot:
            # Note: self.next_point has been already restored from current iteration, so it has current samples!
            pass
        elif self.resume_point == StatusPoint.next_point:
            # Note: self.next_point has been already restored from current iteration, move on to next iteration!
            pass
        else:
            # in case we have more resuming point in the future
            pass

    ###################################################
    # Re-analyze
    ###################################################
    def reanalyze(self):
        # restore next_point and all_results
        if self.iteration > 0:
            self.next_point_algo.set_state(self.next_point, self.iteration - 1)

            iteration_state = IterationState.restore_state(self.calibration_name, self.iteration - 1)
            self.next_point_algo.restore(iteration_state)

            self.restore_results(self.iteration)
        else:
            self.next_point_algo.cleanup()
            self.all_results = None

        # Empty the results and analyzers
        self.results = {}
        self.analyzers = {}

        # Update status and then plot
        self.status = StatusPoint.commission
        self.plot_iteration()

        # Analyze again!
        self.analyze_iteration()

        # Call all plotters
        self.status = StatusPoint.plot
        self.plot_iteration()

        # update status
        self.status = StatusPoint.next_point

        # Save
        self.save()


    ###################################################
    # Re-plot
    ###################################################
    def replot(self, local_all_results):
        # set status so that plotters know when to plot
        self.status = StatusPoint.plot

        # restore next point
        self.next_point_algo.set_state(self.next_point, self.iteration)
        # restore all_results for current iteration
        self.all_results = local_all_results[local_all_results.iteration <= self.iteration]

        for plotter in self.plotters:
            # [TODO]: need to re-consider this condition
            # if isinstance(plotter, SiteDataPlotter.SiteDataPlotter) and self.iteration != calibManager.latest_iteration:
            #     continue
            plotter.visualize(self)
            gc.collect()  # Have to clean up after matplotlib is done


