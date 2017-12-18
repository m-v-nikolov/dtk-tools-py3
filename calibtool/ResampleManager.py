import json
import os


class ResampleManager:
    def __init__(self, steps, calib_manager, analyzers=None):
        self.steps = steps
        self.calib_manager = calib_manager
        self.analyzers = analyzers or calib_manager.analyzer_list

    def resample(self):
        resample_step = 0
        calibrated_points = self.calib_manager.get_calibrated_points()

        for resampler in self.steps:
            calibrated_points = resampler.resample_and_run(calibrated_points=calibrated_points,
                                                           resample_step=resample_step,
                                                           calib_manager=self.calib_manager,
                                                           analyzers=self.analyzers)
            resample_step += 1

        self.results = calibrated_points

    def write_results(self, filename):
        points = [p.to_dict() for p in self.results]

        if os.path.isdir(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(points, f)


