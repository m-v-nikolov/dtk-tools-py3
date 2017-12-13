from argparse import Namespace

import dtk.commands
from dtk.utils.builders.sweep import GenericSweepBuilder

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
        overrides_list = [point.to_dict() for point in points]
        sweep_builder = GenericSweepBuilder.from_list_of_override_dicts(overrides_list)
        mod = run_args.loaded_module
        run_sim_args = {
            'exp_name': mod.calib_manager.name + '_resample_step_%d' % resample_step,
            'exp_builder': sweep_builder,
            'config_builder': mod.calib_manager.config_builder
        }
        setattr(mod, 'run_sim_args', run_sim_args)

        # run simulations at the provided points
        experiment = dtk.commands.run(args=run_args, unknownArgs=unknown_args)
        return experiment

    def _analyze(self, experiment, analyzer_path, unknown_args):
        """
        This method is the in-common route for Resamplers to analyze simulations for liklihood.
        :param experiment: the experiment to analyze, should be from self._run()
        :param analyzer_path: The liklihood analyzer to use
        :return: resampled points with computed liklihood added
        """

        # analyze the provided experiment to compute liklihoods
        analyze_args = {
            'itemids': experiment.exp_id,
            'analyzer': analyzer_path
        }
        analyze_args = Namespace(kwargs=analyze_args)
        dtk.commands.analyze(args=analyze_args, unknownArgs=unknown_args)

        # finesse the resampled points with liklihoods as needed and return for use elsewhere
        resampled_points = some_stuff # ck4
        return resampled_points

    def resample_and_run(self, calibrated_points, analyzer_path, resample_step, run_args, unknown_args):
        """
        Canonical entry method for using the resampler.
        :param calibrated_points:
        :return:
        """
        # 1. resample
        points_to_run = self._resample(calibrated_points=calibrated_points)

        # 2. run simulations
        self.experiment = self._run(points=points_to_run, resample_step=resample_step,
                                    run_args=run_args, unknown_args=unknown_args)

        # 3. analyze simulations for liklihood
        self.resampled_points = self._analyze(experiment=self.experiment, analyzer_path=analyzer_path,
                                              unknown_args=unknown_args)

        return self.resampled_points
