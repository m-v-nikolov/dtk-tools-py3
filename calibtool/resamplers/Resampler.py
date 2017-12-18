from abc import ABCMeta, abstractmethod

from simtools.AnalyzeManager.AnalyzeManager import AnalyzeManager
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory


class Resampler (metaclass=ABCMeta):
    def __init__(self):
        pass

    @abstractmethod
    def _resample(self, calibrated_points):
        pass

    def _run(self, points, calib_manager, resample_step):
        """
        This run method is for running simulations, which is the in-common part of resampling.
        :param points: The points to run simulations at.
        :return: The Experiment object for these simulations
        """
        # create a sweep where each point is a separate sim
        point_dicts = [point.to_value_dict() for point in points]

        # ck4, the number of replicates must be 1 for HIV for now; the general solution should allow a user-selected
        # replicate count, so long as their likelihood analyzer can handle > 1 replicates.
        exp_builder = calib_manager.exp_builder_func(point_dicts, n_replicates=1)

        # Create an experiment manager
        manager = ExperimentManagerFactory.from_cb(calib_manager.config_builder)
        manager.run_simulations(exp_name=calib_manager.name + '_resample_step_%d' % resample_step,
                                blocking=True, exp_builder=exp_builder)

        return manager.experiment

    def _analyze(self, experiment, analyzers, points_ran):
        """
        This method is the in-common route for Resamplers to analyze simulations for liklihood.
        :param experiment: the experiment to analyze, should be from self._run()
        :param analyzer_path: The liklihood analyzer to use
        :param points_ran: Points objects that were just _run()
        :return: The supplied points_ran with their .likelihood attribute set
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
        return points_ran

    def resample_and_run(self, calibrated_points, resample_step, calib_manager, analyzers):
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
        points_to_run = self._resample(calibrated_points=calibrated_points)

        # # 2. run simulations
        self.experiment = self._run(points=points_to_run, resample_step=resample_step, calib_manager=calib_manager)

        # 3. analyze simulations for likelihood
        self.resampled_points = self._analyze(experiment=self.experiment, analyzers=analyzers, points_ran=points_to_run)

        return self.resampled_points
