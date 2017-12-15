from argparse import Namespace

import dtk.commands

class Resampler:
    def __init__(self):
        pass

    def _resample(self, calibrated_points):
        raise Exception('Subclasses of Resampler must define their own _resample() method')

    def _run(self, points, resample_step, run_args, unknown_args):
        """
        This run method is for running simulations, which is the in-common part of resampling.
        :param points: The points to run simulations at.
        :return: The Experiment object for these simulations
        """
        run_args.blocking = True

        # create a sweep where each point is a separate sim to perform and make the calibration script look like
        # a dtk tools run script
        point_dicts = [point.to_dict(only_key='Value') for point in points]
        mod = run_args.loaded_module

        # ck4, the number of replicates must be 1 for HIV for now; the general solution should allow a user-selected
        # replicate count, so long as their likelihood analyzer can handle > 1 replicates.
        exp_builder = mod.calib_manager.exp_builder_func(point_dicts, n_replicates=1)

        run_sim_args = {
            'exp_name': mod.calib_manager.name + '_resample_step_%d' % resample_step,
            'exp_builder': exp_builder,
            'config_builder': mod.calib_manager.config_builder
        }
        setattr(mod, 'run_sim_args', run_sim_args)

        # run simulations at the provided points
        experiment = dtk.commands.run(args=run_args, unknownArgs=unknown_args)
        return experiment

    def _analyze(self, experiment, analyzer_path, points_ran, unknown_args):
        """
        This method is the in-common route for Resamplers to analyze simulations for liklihood.
        :param experiment: the experiment to analyze, should be from self._run()
        :param analyzer_path: The liklihood analyzer to use
        :param points_ran: Points objects that were just _run()
        :return: The supplied points_ran with their .likelihood attribute set
        """

        # analyze the provided experiment to compute likelihoods
        analyze_args = {
            'itemids': experiment.exp_id,
            'analyzer': analyzer_path,
            'batch_name': None, # ck4, eventually expose this to 'calibtool resample' commandline in case someone wants to use it
            'force': False # ck4, ???, eventually expose this to 'calibtool resample' commandline in case someone wants to use it
        }
        analyze_args = Namespace(**analyze_args)
        analyze_manager = dtk.commands.analyze(args=analyze_args, unknownArgs=unknown_args)

        # The provided likelihood analyzer MUST set self.result to be a list of Point objects
        # with the .likelihood attribute set to the likelihood value in its .finalize() method.
        results = analyze_manager.analyzers[0].result

        points_with_likelihoods = points_ran
        # ck4, Here: the likelihood results from the analyzer must be obtained and added to points_with_likelihoods
        # as the .likelihood attribute of each Point.

        # verify that the returned points all have a likelihood attribute set
        likelihoods_are_missing = True in {point.likelihood is None for point in points_with_likelihoods}
        if likelihoods_are_missing:
            raise Exception('At least one Point object returned by the provided analyzer does not have '
                            'its .likelihood attribute set.')
        return points_with_likelihoods

    def resample_and_run(self, calibrated_points, analyzer_path, resample_step, run_args, unknown_args):
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
        self.experiment = self._run(points=points_to_run, resample_step=resample_step,
                                    run_args=run_args, unknown_args=unknown_args)


        # # ck4 remove block after debug
        # from simtools.Utilities.Experiments import retrieve_experiment
        # self.experiment = retrieve_experiment(exp_id='fe061e9e-26e1-e711-80c6-f0921c167864')

        # 3. analyze simulations for likelihood
        self.resampled_points = self._analyze(experiment=self.experiment, analyzer_path=analyzer_path,
                                              points_ran=points_to_run, unknown_args=unknown_args)

        return self.resampled_points
