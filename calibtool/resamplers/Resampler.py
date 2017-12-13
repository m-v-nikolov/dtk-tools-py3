import dtk.commands

class Resampler(object):
    def __init__(self):
        pass

    def _resample(self, calibrated_points):
        raise Exception('Subclasses of Resampler must define their own _resample() method')

    def _run(self, points):
        """
        This run method is for running simulations, which is the in-common part of resampling.
        :param points: The points to run simulations at.
        :return: The Experiment object for these simulations
        """

        # run simulations at the provided points
        args = None # set these arg objects properly, ck4, MUST SET BLOCKING=TRUE
        unknownArgs = None
        experiment = dtk.commands.run(args, unknownArgs)
        return experiment

    def _analyze(self, experiment, analyzer_path):
        """
        This method is the in-common route for Resamplers to analyze simulations for liklihood.
        :param experiment: the experiment to analyze, should be from self._run()
        :param analyzer_path: The liklihood analyzer to use
        :return: resampled points with computed liklihood added
        """
        from simtools.AnalyzeManager.AnalyzeManager import AnalyzeManager

        # analyze the provided experiment to compute liklihoods
        analyze_manager = AnalyzeManager(exp_list=[experiment], analyzers=[analyzer_path])
        args = None  # set these arg objects properly, including the analyze manager just created, ck4
        unknownArgs = None
        dtk.commands.analyze(args, unknownArgs)

        # finesse the resampled points with liklihoods as needed and return for use elsewhere
        resampled_points = some_stuff # ck4
        return resampled_points

    def resample_and_run(self, calibrated_points, analyzer_path):
        """
        Canonical entry method for using the resampler.
        :param calibrated_points:
        :return:
        """
        # 1. resample
        points_to_run = self._resample(calibrated_points=calibrated_points)

        # 2. run simulations
        self.experiment = self._run(points=points_to_run)

        # 3. analyze simulations for liklihood
        self.resampled_points = self._analyze(experiment=self.experiment, analyzer_path=analyzer_path)

        return self.resampled_points
