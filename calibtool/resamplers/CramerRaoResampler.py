import os
from calibtool.resamplers.BaseResampler import BaseResampler
from calibtool.algorithms.FisherInfMatrix import FisherInfMatrix, plot_cov_ellipse


class CramerRaoResampler(BaseResampler):
    def __init__(self, n_resampling_points, **kwargs):
        """
        :param n_resampling_points: The number of resampled points to generate
        :param kwargs: These are arguments passed directly to the underlying resampling routine.
        """
        super().__init__()
        self.n_resampling_points = n_resampling_points # the number of points to resample/generate
        self.resample_kwargs = kwargs

    def resample(self, calibrated_points):
        """
        :return:
        """

        raise Exception('CramerRao resample method not yet defined. Ask Atiye.')
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
        plot_cov_ellipse(Covariance[0:2, 0:2], center[0:2], nstd=1, alpha=0.6, color='green')
        plt.xlim(Xmin[0], Xmax[0])
        plt.ylim(Xmin[1], Xmax[1])
        plt.xlabel('X', fontsize=14)
        plt.ylabel('Y', fontsize=14)

        # save fig to file
        fig3.savefig(os.path.join(self.output_location, 'CramerRao.png'))

        plt.show()


