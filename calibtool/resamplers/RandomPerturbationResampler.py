import os

from calibtool.algorithms.FisherInfMatrix import perturbed_points
from calibtool.resamplers.BaseResampler import BaseResampler
from calibtool.resamplers.CalibrationPoint import CalibrationPoint, CalibrationParameter

class RandomPerturbationResampler(BaseResampler):
    def __init__(self, **kwargs):
        """
        :param kwargs: These are arguments passed directly to the perturbed points generation routine.
        """
        super().__init__()
        self.resample_kwargs = kwargs

    def resample(self, calibrated_points, selection_values, initial_calibration_points):
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
        n_calibrated_points = len(calibrated_points)
        if n_calibrated_points != 1:
            raise Exception('RandomPerturbationResampler requires there to be exactly one input point. There are %d'
                            % n_calibrated_points)
        self.center_point = initial_calibration_points[0]
        self.resampled_points_df = self.generate_perturbed_points(self.center_point)

        # transform perturbed_points to CalibrationPoint objects
        self.resampled_points = self._transform_df_points_to_calibrated_points(self.center_point,
                                                                               self.resampled_points_df)

        return self.resampled_points


    def post_analysis(self, resampled_points, analyzer_results):
        super().post_analysis(resampled_points, analyzer_results)

        # write the initial center point for later reference
        output_filename = os.path.join(self.output_location, 'center.json')
        self.center_point.write_point(output_filename)

        # save new_points dataframe to csv file
        output_filename = os.path.join(self.output_location, 'data.csv')
        self.resampled_points_df.to_csv(output_filename)

        # save perturbed_points with likelihood to file
        resampled_points_df_ll = self.resampled_points_df.copy()
        resampled_points_df_ll.insert(4, 'LL', analyzer_results)
        output_filename = os.path.join(self.output_location, 'LLdata.csv')
        resampled_points_df_ll.to_csv(output_filename)


    def generate_perturbed_points(self, center_point):
        """
        given center and generate perturbed points
        """

        # retrieve settings
        df = center_point.to_dataframe()
        Names = df['Name'].tolist()
        Center = df['Value'].values
        Xmin = df['Min'].values
        Xmax = df['Max'].values

        # get perturbed points
        df_perturbed_points = perturbed_points(Center, Xmin, Xmax, **self.resample_kwargs)

        # re-name columns
        self.selection_columns = ['i(1to4)','j(1toN)','k(1toM)','run_number'] # to be made available in the following resampling
        df_perturbed_points.columns = self.selection_columns + Names

        return df_perturbed_points



