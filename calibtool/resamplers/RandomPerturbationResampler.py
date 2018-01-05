import os

from calibtool.algorithms.FisherInfMatrix import perturbed_points
from calibtool.resamplers.BaseResampler import BaseResampler
from calibtool.resamplers.CalibrationPoint import CalibrationPoint, CalibrationParameter

class RandomPerturbationResampler(BaseResampler):
    def __init__(self, n_resampling_points=None):
        super().__init__(n_resampling_points=n_resampling_points)


    def resample(self, calibrated_points, n_points):
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
        self.center_point = calibrated_points[0]
        self.resampled_points_df = self.generate_perturbed_points(self.center_point, n_points)

        # transform perturbed_points to CalibrationPoint objects
        self.resampled_points = self.transform_perturbed_points_to_calibrated_points(self.center_point,
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


    def generate_perturbed_points(self, center_point, n_points):
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
        if self.n_resampling_points is None:
            df_perturbed_points = perturbed_points(Center, Xmin, Xmax)
        else:
            df_perturbed_points = perturbed_points(Center, Xmin, Xmax, N=self.n_resampling_points)
        # re-name columns
        df_perturbed_points.columns = ['i', 'j', 'k', 'l'] + Names

        return df_perturbed_points


    def transform_perturbed_points_to_calibrated_points(self, calibrated_point, df_perturbed_points):
        # get parameter names
        df_point = calibrated_point.to_dataframe()
        param_names = df_point['Name'].tolist()

        # retrieve parameters settings
        get_settings = calibrated_point.get_settings()

        # build calibration points
        calibrated_points = []
        for index, row in df_perturbed_points.iterrows():
            parameters = []
            for name in param_names:
                paramer = CalibrationParameter(name, get_settings[name]['min'], get_settings[name]['max'], row[name])
                parameters.append(paramer)

            calibrated_points.append(CalibrationPoint(parameters))

        return calibrated_points
