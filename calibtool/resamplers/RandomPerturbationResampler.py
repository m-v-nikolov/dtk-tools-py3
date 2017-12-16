from calibtool.resamplers.Resampler import Resampler

class RandomPerturbationResampler(Resampler):

    # ck4, add any desired args for this initializer
    def __init__(self):
        pass

    def _resample(self, calibrated_points):
        """
        Takes in a list of 1+ Point objects and returns method-specific resampled points as a list of Point objects
        The resultant Point objects should be copies of the input Points BUT with Value overridden on each, e.g.:

        new_point = Point.copy(one_of_the_input_calibrated_points)
        for param in new_point.list_params():
          new_point.set_param_value(param, value=SOME_NEW_VALUE)

        :param calibrated_points: input points for this resampling method
        :return: a list of resampled Point objects
        """

        # method-specific stuff here
        raise Exception('RandomPerturbationResampler _resample() method is incomplete.')
        return new_points