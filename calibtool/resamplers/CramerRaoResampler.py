import os
import numpy as np
import pandas as pd
from calibtool.resamplers.BaseResampler import BaseResampler
from calibtool.algorithms.FisherInfMatrix import FisherInfMatrix, plot_cov_ellipse, sample_cov_ellipse


class CramerRaoResampler(BaseResampler):
    def __init__(self, **kwargs):
        """
        :param n_resampling_points: The number of resampled points to generate
        :param kwargs: These are arguments passed directly to the underlying resampling routine.
        """
        super().__init__()
        # self.n_resampling_points = n_resampling_points # the number of points to resample/generate
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

        # selection_values: a DataFrame with columns relevant to selection of calibrated_points

        center_point = initial_calibration_points[0]

        # convert input points to DataFrames
        calibrated_points_df = []
        for i in range(len(calibrated_points)):
            print('Calibrated point %d:\n%s' % (i, calibrated_points[i].to_value_dict()))
            calibrated_points_df.append(calibrated_points[i].to_value_dict())
        calibrated_points_df = pd.DataFrame(calibrated_points_df)
        original_column_names = calibrated_points_df.columns
        calibrated_points_df = selection_values.join(calibrated_points_df)

        # temporary, generic column names for the actual parameter names
        theta_column_names = ['theta%d'%i for i in range(len(original_column_names))]
        temp_columns = list(selection_values.columns) + theta_column_names
        print('setting columns to: %s' % temp_columns)
        calibrated_points_df.columns = temp_columns

        # same as calibrated_points_df but with a LL column on the end
        likelihood_df = pd.DataFrame([{'LL': point.likelihood} for point in calibrated_points])
        likelihood_df = calibrated_points_df.join(likelihood_df)

        # Do the resampling

        # center_point is a list of param values at the center point, must be ordered exactly as calibrated_points_df column-wise
        # print('Center point as value dict:\n%s' % center_point.to_value_dict())
        # print('cpdf:\n%s' % pd.DataFrame([center_point.to_value_dict()]))
        # print('cpdf2:\n%s' % list(pd.DataFrame([center_point.to_value_dict()])))
        # print('cpdf3:\n%s' % list(pd.DataFrame([center_point.to_value_dict()]).as_matrix()[0]))
        center_point_as_list = list(pd.DataFrame([center_point.to_value_dict()]).as_matrix()[0]) # ck4, is this the same ordering as with calibrated_points_df?
        print('center_point_as_list:\n%s' % center_point_as_list)
        fisher_inf_matrix = FisherInfMatrix(calibrated_points[0].dimensionality, calibrated_points_df, likelihood_df)
        # print(fisher_inf_matrix)
        covariance = np.linalg.inv(fisher_inf_matrix)
        # print(covariance)

        resampled_points_list = sample_cov_ellipse(covariance, center_point_as_list, **self.resample_kwargs)
        print('A. There are %d resampled points.' % len(resampled_points_list))
        # convert resampled points to a list of CalibrationPoint objects
        resampled_points_df = pd.DataFrame(data=resampled_points_list, columns=original_column_names)
        resampled_points = self._transform_df_points_to_calibrated_points(center_point,
                                                                          resampled_points_df)

        print('B. There are %d resampled points.' % len(resampled_points))
        # return reampled points
        return resampled_points


    def post_analysis(self, resampled_points, analyzer_results):
        super().post_analysis(resampled_points, analyzer_results)
        raise Exception('CramerRao post_analysis method not yet defined, if needed.')

        # # plotting
        # df_point = center_point.to_dataframe()
        # center = df_point['Value'].values  # nparray
        # Xmin = df_point['Min'].values  # nparray
        # Xmax = df_point['Max'].values  # nparray
        # self.plot(center, Xmin, Xmax, df_perturbed_points, df_perturbed_points_ll)


    def plot(self, center, Xmin, Xmax, df_perturbed_points, ll):
        """
        :param center:
        :param Xmin:
        :param Xmax:
        :param df_perturbed_points:
        :param ll: df_perturbed_points with likelihood
        :return:
        """
        import numpy as np
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        Fisher = FisherInfMatrix(center, df_perturbed_points, ll)
        Covariance = np.linalg.inv(Fisher)

        print("eigs of fisher: ", np.linalg.eigvals(Fisher))
        print("eigs of Covariance: ", np.linalg.eigvals(Covariance))

        fig3 = plt.figure('CramerRao')
        ax = plt.subplot(111)
        x, y = center[0:2]
        plt.plot(x, y, 'g.')
        plot_cov_ellipse(Covariance[0:2, 0:2], center[0:2], nstd=3, alpha=0.6, color='green')
        plt.xlim(Xmin[0], Xmax[0])
        plt.ylim(Xmin[1], Xmax[1])
        plt.xlabel('X', fontsize=14)
        plt.ylabel('Y', fontsize=14)

        # save fig to file
        fig3.savefig(os.path.join(self.output_location, 'CramerRao.png'))

        plt.show()


