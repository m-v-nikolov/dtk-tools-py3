from abc import ABCMeta, abstractmethod
import os
from simtools.AnalyzeManager.AnalyzeManager import AnalyzeManager
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory

class BaseResampler(metaclass=ABCMeta):
    def __init__(self):
        self.calib_manager = None # needs setting externally
        self.output_location = None # must be set via setter below


    # strictly required to be defined in subclasses
    @abstractmethod
    def resample(self, calibrated_points):
        pass


    # extend if desired in subclasses
    def post_analysis(self, resampled_points, analyzer_results):
        os.makedirs(self.output_location, exist_ok=True)


    def set_calibration_manager(self, calib_manager):
        self.calib_manager = calib_manager
        self.output_location = os.path.join(calib_manager.name, 'resampling_output')


    def _run(self, points, resample_step):
        """
        This run method is for running simulations, which is the in-common part of resampling.
        :param points: The points to run simulations at.
        :return: The Experiment object for these simulations
        """
        # create a sweep where each point is a separate sim
        if not self.calib_manager:
            raise Exception('calibration manager has not set for resampler. Cannot generate simulations.')

        point_dicts = [point.to_value_dict() for point in points]

        # ck4, the number of replicates must be 1 for HIV for now; the general solution should allow a user-selected
        # replicate count, so long as their likelihood analyzer can handle > 1 replicates.
        exp_builder = self.calib_manager.exp_builder_func(point_dicts, n_replicates=1)

        # Create an experiment manager
        manager = ExperimentManagerFactory.from_cb(self.calib_manager.config_builder)
        exp_name = self.calib_manager.name + '_resample_step_%d' % resample_step
        manager.run_simulations(exp_name=exp_name, blocking=True, exp_builder=exp_builder)

        return manager


    def _analyze(self, experiment, analyzers, points_ran):
        """
        This method is the in-common route for Resamplers to analyze simulations for liklihood.
        :param experiment: the experiment to analyze, should be from self._run()
        :param points_ran: Points objects that were just _run()
        :return: The supplied points_ran with their .likelihood attribute set, AND the direct results of the analyzer
                 as a list.
        """
        am = AnalyzeManager(analyzers=analyzers, exp_list=experiment)
        am.analyze()

        # The provided likelihood analyzer MUST set self.result to be a list of Point objects
        # with the .likelihood attribute set to the likelihood value in its .finalize() method.
        results = am.analyzers[0].result.tolist()

        for i in range(len(results)):
            # Add the likelihood
            points_ran[i].likelihood = results[i]

        # verify that the returned points all have a likelihood attribute set
        likelihoods_are_missing = True in {point.likelihood is None for point in points_ran}
        if likelihoods_are_missing:
            raise Exception('At least one Point object returned by the provided analyzer does not have '
                            'its .likelihood attribute set.')

        return points_ran, results


    def resample_and_run(self, calibrated_points, resample_step):
        """
        Canonical entry method for using the resampler.
        :param calibrated_points:
        :return:
        """
        # 1. resample
        # The user-provided _resample() method in Resampler subclasses must set the 'Value' in each Point object dict
        # for keying off of in the _run() method above.
        # Any _resample() methodology that depends on the likelihood of the provided points should reference
        #    the 'likelihood' attribute on the Point objects (e.g., use mypoint.likelihood, set it in the analyer
        #    return points.
        points_to_run = self.resample(calibrated_points=calibrated_points)

        # # 2. run simulations
        experiment_manager = self._run(points=points_to_run, resample_step=resample_step)
        experiment_manager.wait_for_finished()

        # 3. analyze simulations for likelihood
        self.resampled_points, self.analyzer_results = self._analyze(experiment=experiment_manager.experiment,
                                                                     analyzers=self.calib_manager.analyzer_list,
                                                                     points_ran=points_to_run)

        # 4. perform any post-analysis processing, if defined
        self.post_analysis(self.resampled_points, self.analyzer_results)

        return self.resampled_points
