from calibtool.resamplers import Resampler

class CramerRaoResampler(Resampler):
    def __init__(self):  # ck4, add any desired args for this class
        self.method = 'cramer-rao'
        # self.some_arg = some_arg , ck4

    def _resample(self, calibrated_points):
        """
        Takes in 1+ points and returns method-specific resampled points
        :param calibrated_points: input points for this resampling method
        :return: resampled points
        """

        # method-specific stuff here
        new_points = some_stuff2 # ck4
        return new_points
    