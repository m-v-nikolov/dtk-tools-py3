import copy

from calibtool.resamplers.Resampler import Resampler

class RandomPerturbationResampler(Resampler):

    # ck4, add any desired args for this initializer
    def __init__(self):
        super().__init__()

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
        new_points = []

        for pt in calibrated_points:
            pt1 = copy.deepcopy(pt)

            for param in pt1.parameters:
                param.value += 0.5
            new_points.append(pt)
            new_points.append(pt1)


        return new_points