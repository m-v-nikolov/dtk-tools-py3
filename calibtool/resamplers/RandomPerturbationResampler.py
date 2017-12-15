from calibtool.resamplers.Resampler import Resampler

class RandomPerturbationResampler(Resampler):

    # ck4, add any desired args for this initializer
    def __init__(self):
        pass

    def _resample(self, calibrated_points):
        """
        Takes in 1+ Point objects and returns method-specific resampled points
        :param calibrated_points: input points for this resampling method
        :return: a list of resampled Point objects
        """

        # method-specific stuff here
        raise Exception('RandomPerturbationResampler _resample() method is incomplete.')
        return new_points