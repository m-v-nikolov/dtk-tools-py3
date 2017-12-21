import os
from calibtool.resamplers.BaseResampler import BaseResampler
from simtools.AnalyzeManager.AnalyzeManager import AnalyzeManager
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from calibtool.resamplers.Point import CalibrationPoint, CalibrationParameter
from calibtool.algorithms.FisherInfMatrix import FisherInfMatrix, plot_cov_ellipse, perturbed_points


class CramerRaoResampler(BaseResampler):
    def __init__(self,  calib_manager):
        super(CramerRaoResampler, self).__init__(calib_manager)

    def resample(self):
        """
        :return:
        """
        # collect the point from last iteration
        calibrated_points = self.get_calibrated_points()

        # consider single point as center point
        center_point = calibrated_points[0]

        # generate perturbed points
        df_perturbed_points = self.generate_perturbed_points(center_point)

        # transform perturbed_points to calibration points
        resampled_points = self.transform_perturbed_points_to_calibrated_points(center_point, df_perturbed_points)

        # run simulations
        experiment = self._run(points=resampled_points)

        # analyze simulations for likelihood
        results, ll = self._analyze(experiment=experiment, analyzers=self.calib_manager.analyzer_list, points_ran=resampled_points)

        # save perturbed_points with likelihood to file
        df_perturbed_points_ll = df_perturbed_points.copy()
        df_perturbed_points_ll['ll'] = ll

        folder_path = os.path.join(self.calib_manager.name, 'Resampling Output')
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
        df_perturbed_points_ll.to_csv(os.path.join(folder_path, 'LLdata.csv'))

        # plotting
        df_point = center_point.to_dataframe()
        center = df_point['Value'].values   #nparray
        Xmin = df_point['Min'].values       #nparray
        Xmax = df_point['Max'].values       #nparray

        self.plot(center, Xmin, Xmax, df_perturbed_points, df_perturbed_points_ll)

    def get_calibrated_points(self):
        """
        Retrieve information about the most recent (final completed) iteration's calibrated point,
        merging from the final IterationState.json and CalibManager.json .
        :return:
        """
        n_points = 1 # ck4, hardcoded for now for HIV purposes, need to determine how to get this from the CalibManager

        calib_data = self.calib_manager.read_calib_data()

        iteration = self.calib_manager.get_last_iteration()
        iteration_data = self.calib_manager.read_iteration_data(iteration=iteration)

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
        df_perturbed_points = perturbed_points(Center, Xmin, Xmax)

        # re-name columns
        df_perturbed_points.columns = ['i', 'j', 'k', 'l'] + Names

        # save to csv file
        folder_path = os.path.join(self.calib_manager.name, 'Resampling Output')
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
        df_perturbed_points.to_csv(os.path.join(folder_path, 'data.csv'))

        return df_perturbed_points

    def _run(self, points):
        """
        This run method is for running simulations, which is the in-common part of resampling.
        :param points: The points to run simulations at.
        :return: The Experiment object for these simulations
        """

        # create a sweep where each point is a separate sim
        point_dicts = [point.to_value_dict() for point in points]

        # ck4, the number of replicates must be 1 for HIV for now; the general solution should allow a user-selected
        # replicate count, so long as their likelihood analyzer can handle > 1 replicates.
        exp_builder = self.calib_manager.exp_builder_func(point_dicts, n_replicates=1)

        # Create an experiment manager
        manager = ExperimentManagerFactory.from_cb(self.calib_manager.config_builder)
        manager.run_simulations(exp_name=self.calib_manager.name + '_resampled', blocking=True, exp_builder=exp_builder)

        return manager.experiment

    def _analyze(self, experiment, analyzers, points_ran):
        """
        This method is the in-common route for Resamplers to analyze simulations for liklihood.
        :param experiment: the experiment to analyze, should be from self._run()
        :param analyzer_path: The liklihood analyzer to use
        :param points_ran: Points objects that were just _run()
        :return: The supplied points_ran with their .likelihood attribute set
        """
        am = AnalyzeManager(analyzers=analyzers, exp_list=experiment)
        am.analyze()

        # The provided likelihood analyzer MUST set self.result to be a list of Point objects
        # with the .likelihood attribute set to the likelihood value in its .finalize() method.
        results = am.analyzers[0].result.tolist()

        for i in range(len(results)):
            # Add the likelihood
            points_ran[i].likelihood = results[i]

        # verify that the returned points all have a likelihood attribute set
        likelihoods_are_missing = True in {point.likelihood is None for point in points_ran}
        if likelihoods_are_missing:
            raise Exception('At least one Point object returned by the provided analyzer does not have '
                            'its .likelihood attribute set.')

        return points_ran, results

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

        folder_path = os.path.join(self.calib_manager.name, 'Resampling Output')
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
        fig3.savefig(os.path.join(folder_path, 'CramerRao.png'))

        plt.show()


