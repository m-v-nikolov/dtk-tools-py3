from calibtool.resamplers.CalibrationPoint import CalibrationPoint, CalibrationParameter
from calibtool.resamplers.CalibrationPoints import CalibrationPoints

class ResampleManager:
    def __init__(self, steps, calibration_manager):
        for resampler in steps:
            resampler.set_calibration_manager(calibration_manager)
        self.steps = steps
        self.calibration_manager = calibration_manager

    def resample_and_run(self):
        # set the initial parameter points to resample from
        calibrated_points = self.get_calibrated_points()

        resample_step = 0
        for resampler in self.steps:
            calibrated_points = resampler.resample_and_run(calibrated_points=calibrated_points,
                                                           resample_step=resample_step)
                                                           # run_args=run_args,
                                                           # unknown_args=unknown_args)
            resample_step += 1
        self.results = calibrated_points

    def write_results(self, filename):
        CalibrationPoints(points=self.results).write(filename=filename)


    def get_calibrated_points(self):
        """
        Retrieve information about the most recent (final completed) iteration's calibrated point,
        merging from the final IterationState.json and CalibManager.json .
        :return:
        """
        n_points = 1 # ck4, hardcoded for now for HIV purposes, need to determine how to get this from the CalibManager

        calib_data = self.calibration_manager.read_calib_data()

        iteration = self.calibration_manager.get_last_iteration()
        iteration_data = self.calibration_manager.read_iteration_data(iteration=iteration)

        final_samples = calib_data['final_samples']
        iteration_metadata = iteration_data.next_point['params']

        # Create the list of points and their associated parameters
        points = list()
        for i in range(0, n_points):
            parameters = list()
            for param_metadata in iteration_metadata:
                param_metadata["Value"] = final_samples[param_metadata["Name"]][0]
                parameters.append(CalibrationParameter.from_dict(param_metadata))
            points.append(CalibrationPoint(parameters))

        return points