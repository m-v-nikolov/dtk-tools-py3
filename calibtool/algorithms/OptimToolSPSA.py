from __future__ import division

import logging

import numpy as np
import pandas as pd

from calibtool.algorithms.NextPointAlgorithm import NextPointAlgorithm

logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


class OptimToolSPSA(NextPointAlgorithm):
    """
    OptimTool

    The basic idea of OptimTool is
    """

    def cleanup(self):
        pass

    def __init__(self, params, constrain_sample_fn, comps_per_iteration=10):

        self.args = locals()  # Store inputs in case set_state is called later and we want to override with new (user) args
        del self.args['self']
        self.need_resolve = False

        self.constrain_sample_fn = constrain_sample_fn

        self.state = pd.DataFrame(columns=['Iteration', 'Parameter', 'Center', 'Hessian', 'Min', 'Max', 'Dynamic'])
        self.state['Iteration'] = self.state['Iteration'].astype(int)

        self.params = params  # TODO: Check min <= center <= max
        self.comps_per_iteration = int(comps_per_iteration)

        self.Xmin = {p['Name']: p['Min'] for p in self.params}
        self.Xmax = {p['Name']: p['Max'] for p in self.params}
        self.Dynamic = {p['Name']: p['Dynamic'] for p in self.params}
        self.n_dimensions = None
        self.data = pd.DataFrame()

    def resolve_args(self, iteration):
        # Have args from user and from set_state.
        # Note this is called only right before commissioning a new iteration, likely from 'resume'

        # TODO: be more sensitive with params, user could have added or removed variables, need to adjust
        # TODO: Check min <= center <= max for params
        # TODO: could clean this up with a helper function
        self.params = self.args[
            'params'] if 'params' in self.args else self.params  # Guess may move, but should be ignored
        self.comps_per_iteration = self.args[
            'comps_per_iteration'] if 'comps_per_iteration' in self.args else self.comps_per_iteration

        self.n_dimensions = len(self.params)
        self.Xmin = {p['Name']: p['Min'] for p in self.params}
        self.Xmax = {p['Name']: p['Max'] for p in self.params}
        self.Dynamic = {p['Name']: p['Dynamic'] for p in self.params}

        self.need_resolve = False

        """
        # TODO: Allow user to override current 'Center' value
        state_by_iter = self.state.set_index('Iteration')
        if iteration == 0:
            # Not sure this would happen, but just in case
            cur_val = {p['Name']:p['Guess'] for p in self.params}
        else:
            cur_val = {s['Parameter']:s['Center'] for (i,s) in state_by_iter.loc[iteration-1].iterrows()}

        iter_state = pd.DataFrame(columns=['Iteration', 'Parameter', 'Center', 'Min', 'Max', 'Dynamic'])
        for param in self.params:
            iter_state.loc[len(iter_state)] = [iteration, param['Name'], cur_val[param['Name']], param['Min'], param['Max'], param['Dynamic']]

        self.state = self.state.loc[:iteration-1]
        self.state.reset_index(inplace=True)
        self.state = pd.concat([self.state, iter_state], ignore_index=True)
        self.state['Iteration'] = self.state['Iteration'].astype(int)

        with pd.option_context("display.max_rows", 500, "display.max_columns", 500):
            print(self.state)
            raw_input('resolve_args')
        """

    def _get_X_center(self, iteration):
        state_by_iter = self.state.reset_index(drop=True).set_index(['Iteration', 'Parameter'])
        assert (iteration in state_by_iter.index.get_level_values('Iteration'))
        return state_by_iter.loc[iteration]['Center']

    def _get_Hessian(self, iteration):
        state_by_iter = self.state.reset_index(drop=True).set_index(['Iteration', 'Parameter'])
        assert (iteration in state_by_iter.index.get_level_values('Iteration'))
        return state_by_iter.loc[iteration]['Hessian']

    def add_samples(self, samples, iteration):
        samples_cpy = samples.copy()
        samples_cpy.index.name = '__sample_index__'
        samples_cpy['Iteration'] = iteration
        samples_cpy.reset_index(inplace=True)

        self.data = pd.concat([self.data, samples_cpy], ignore_index=True)
        self.data['__sample_index__'] = self.data['__sample_index__'].astype(int)

    def get_samples_for_iteration(self, iteration):
        # Update args
        if self.need_resolve:
            self.resolve_args(iteration)

        if iteration == 0:
            # Choose initial samples
            samples = self.choose_initial_samples()
        else:
            # Regress inputs and results from previous iteration
            # Move X_center, choose samples, save in dataframe
            samples = self.StochasticNewtonRaphson(iteration)

        samples.reset_index(drop=True, inplace=True)
        return self.generate_samples_from_df(samples)

    def clamp(self, X):

        print("X.before:\n{}".format(X))

        # X should be a data frame
        for pname in X.columns:
            X[pname] = np.minimum(self.Xmax[pname], np.maximum(self.Xmin[pname], X[pname]))

        return X

    def set_results_for_iteration(self, iteration, results):
        results = results.total.tolist()
        logger.info('%s: Choosing samples at iteration %d:', self.__class__.__name__, iteration)
        logger.debug('Results:\n%s', results)

        data_by_iter = self.data.set_index('Iteration')
        if iteration + 1 in data_by_iter.index.unique():
            # Been here before, reset
            data_by_iter = data_by_iter.loc[:iteration]

            state_by_iter = self.state.set_index('Iteration')
            self.state = state_by_iter.loc[:iteration].reset_index()

        # Store results ... even if changed
        data_by_iter.loc[iteration, 'Results'] = results
        self.data = data_by_iter.reset_index()

    def choose_initial_samples(self):
        self.data = pd.DataFrame(columns=[['Iteration', '__sample_index__', 'Results'] + self.get_param_names()])
        self.data['Iteration'] = self.data['Iteration'].astype(int)
        self.data['__sample_index__'] = self.data['__sample_index__'].astype(int)

        self.n_dimensions = len(self.params)

        iteration = 0

        # Clear self.state in case of resuming iteration 0 from commission
        self.state = pd.DataFrame(columns=['Iteration', 'Parameter', 'Center', 'Hessian', 'Min', 'Max', 'Dynamic'])
        self.state['Iteration'] = self.state['Iteration'].astype(int)

        for param in self.params:
            print (iteration, param['Name'], param['Guess'], param['Min'], param['Max'], param['Dynamic'])
            self.state.loc[len(self.state)] = [iteration, param['Name'], param['Guess'], param['aprioriHessian'],
                                               param['Min'], param['Max'], param['Dynamic']]
            # print(self.state)

        initial_samples = self.choose_and_clamp_samples_for_iteration(iteration)

        self.add_samples(initial_samples, iteration)

        return initial_samples

    def StochasticNewtonRaphson(self, iteration):

        assert (iteration >= 1)

        def proj_spd(A):
            # NOTE: the input matrix is assumed to be symmetric
            d, v = np.linalg.eigh(A)
            A = (v * np.maximum(abs(d), 1e-5)).dot(v.T)
            A = (A + A.T) / 2
            return (A)

        # DYNAMIC ON PREVIOUS ITERATION WHEN COMMISSIONED ...
        state_prev_iter = self.state.set_index('Iteration').loc[iteration - 1]
        dynamic_params = [r['Parameter'] for idx, r in state_prev_iter.iterrows() if r['Dynamic']]

        self.data.set_index('Iteration', inplace=True)
        latest_dynamic_samples = self.data.loc[iteration - 1, dynamic_params].values
        latest_results = self.data.loc[iteration - 1, 'Results'].values

        X_min = np.asarray([self.Xmin[pname] for pname in dynamic_params])
        X_max = np.asarray([self.Xmax[pname] for pname in dynamic_params])

        X_current = latest_dynamic_samples[0]
        X_current_scaled = (X_current - X_min) / (X_max - X_min)

        # H_sign = -1 # Hessian should be neg. semi definite (maximization)
        p = X_current.size
        M = self.comps_per_iteration
        Hessian_elements = [r['Hessian'] for idx, r in state_prev_iter.iterrows() if r['Dynamic']]
        H_current_est = np.diag(Hessian_elements)

        largest_step_size = np.abs(np.array([1] * p) - np.array([0] * p)) / 5

        # optimization parameters
        A0, step = 3, .5
        a0 = step * (1 + A0) ** (0.602)
        a = a0 * (iteration + 1 + A0) ** (-0.602)
        # TODO: assumed here that there is no prior Hessian information 
        w = .8 * (iteration + 1) ** (-.501) if iteration > 1 else 1

        G_avg = np.zeros(shape=(p, M))
        S_avg = np.zeros(shape=(p, p, M))

        for k in range(M):
            np.random.seed()

            thetaPlus = (np.array(latest_dynamic_samples[4 * k + 1]) - X_min) / (X_max - X_min)
            thetaMinus = (np.array(latest_dynamic_samples[4 * k + 2]) - X_min) / (X_max - X_min)
            f_plus = latest_results[4 * k + 1]
            f_minus = latest_results[4 * k + 2]

            Gk = (f_plus - f_minus) / (thetaPlus - thetaMinus)
            G_avg[:, k] = k / (k + 1) * G_avg[:, k - 1] + 1 / (k + 1) * Gk.T

            thetaPlusPlus = (np.array(latest_dynamic_samples[4 * k + 3]) - X_min) / (X_max - X_min)
            thetaMinusPlus = (np.array(latest_dynamic_samples[4 * k + 4]) - X_min) / (X_max - X_min)
            f_PlusPlus = latest_results[4 * k + 3]
            f_MinusPlus = latest_results[4 * k + 4]

            G_p = (f_PlusPlus - f_plus) / (thetaPlusPlus - thetaMinusPlus)
            G_m = (f_MinusPlus - f_minus) / (thetaPlusPlus - thetaMinusPlus)

            Sk = np.dot((1 / (thetaPlus - thetaMinus))[:, None], (G_p - G_m)[None, :])
            S_avg[:, :, k] = k / (k + 1) * S_avg[:, :, k - 1] + 1 / (k + 1) * Sk

        G = G_avg[:, M - 1]
        H_hat = .5 * (S_avg[:, :, M - 1] + S_avg[:, :, M - 1].T)
        H_bar = (1 - w) * H_current_est + w * H_hat
        H_2bar = -1 * proj_spd(-H_bar)  # H_bar#.5*(H_bar - sqrtm(np.linalg.matrix_power(H_bar,2)+1e-6*np.eye(p)))
        H_2bar_INV = np.linalg.inv(H_2bar)

        # update x
        update = H_2bar_INV.dot(G)
        if (np.abs(update) > largest_step_size).any():
            update = np.linalg.norm(largest_step_size) * update / np.linalg.norm(update)

        X_next_scaled = X_current_scaled - a * update  # x_{n+1} = x_n - a_n H_n^{-1} G_n
        X_next = X_next_scaled * (X_max - X_min) + X_min
        Hessian_next = np.diag(H_bar)

        self.data.reset_index(inplace=True)

        old_center = self._get_X_center(iteration - 1)
        old_center_of_dynamic_params = old_center[dynamic_params].values
        new_dynamic_center = X_next.tolist()
        new_center_dict = old_center.to_dict()  # {k:v for k,v in zip(self.get_param_names(), old_center)}
        new_center_dict.update({k: v for k, v in zip(dynamic_params, new_dynamic_center)})

        old_Hessian = self._get_Hessian(iteration - 1)
        old_Hessian_of_dynamic_params = old_Hessian[dynamic_params].values
        new_dynamic_Hessian = Hessian_next.tolist()
        new_Hessian_dict = old_Hessian.to_dict()
        new_Hessian_dict.update({k: v for k, v in zip(dynamic_params, new_dynamic_Hessian)})

        # User may have added or removed params
        param_names = [p['Name'] for p in self.params]
        # Remove -
        new_center_df = {k: v for k, v in new_center_dict.items() if k in param_names}
        new_Hessian_df = {k: v for k, v in new_Hessian_dict.items() if k in param_names}
        # Add -
        new_params = {p['Name']: p['Guess'] for p in self.params if p['Name'] not in new_center_dict}
        new_center_dict.update(new_params)
        new_Hessian_dict.update(new_params)

        # CLAMP
        new_center_df = pd.Series(new_center_dict, name=0).to_frame().transpose()
        new_Hessian_df = pd.Series(new_Hessian_dict, name=0).to_frame().transpose()
        new_center_df = self.clamp(new_center_df)

        # USER CONSTRAINT FN
        new_center_df = new_center_df.apply(self.constrain_sample_fn, axis=1)

        new_state = pd.DataFrame({
            'Iteration': [iteration] * self.n_dimensions,
            'Parameter': new_center_df.columns.values,
            'Center': new_center_df.as_matrix()[0],
            'Hessian': new_Hessian_df.as_matrix()[0],
            'Min': [self.Xmin[pname] for pname in new_center_df.columns.values],
            'Max': [self.Xmax[pname] for pname in new_center_df.columns.values],
            'Dynamic': [self.Dynamic[pname] for pname in new_center_df.columns.values]
        })

        self.state = self.state.query('Iteration < @iteration')
        self.state = pd.concat([self.state, new_state], ignore_index=True)

        samples = self.choose_and_clamp_samples_for_iteration(iteration)
        self.add_samples(samples, iteration)

        return samples

    def choose_and_clamp_samples_for_iteration(self, iteration):
        M = self.comps_per_iteration
        state_by_iter = self.state.set_index('Iteration')
        # Will vary parameters that are 'Dyanmic' on this iteration
        samples = self.sample_simultaneous_perturbation(M, iteration, state_by_iter.loc[iteration])

        # Clamp and constrain
        samples = self.clamp(samples)
        samples = samples.apply(self.constrain_sample_fn, axis=1)

        return samples  # Order shouldn't matter now, so dropped [self.get_param_names()]

    def sample_simultaneous_perturbation(self, M, iteration, state):
        # Pick samples x+c\Delta, x-c\Delta, x+c\Delta+c_tilde\Delta_tilde, x-c\Delta+c_tilde\Delta_tilde

        assert (M > 0)

        dynamic_state = state.query('Dynamic == True')
        dynamic_state_by_param = dynamic_state.set_index('Parameter')

        X_min = np.array([dynamic_state_by_param.loc[pname, 'Min'] for pname in dynamic_state['Parameter']])
        X_max = np.array([dynamic_state_by_param.loc[pname, 'Max'] for pname in dynamic_state['Parameter']])
        X_current = np.array([dynamic_state_by_param.loc[pname, 'Center'] for pname in dynamic_state['Parameter']])

        c0 = .05 * (X_max - X_min) / M ** 0.5

        for i in range(len(c0)):
            while (X_current[i] - 3 * c0[i] < X_min[i]) or (X_current[i] + 3 * c0[i] > X_max[i]):
                c0[i] = .8 * min(X_current[i] - X_min[i], X_max[i] - X_current[i]) / 3

        c = c0 * (iteration + 1) ** (-0.101)
        c_tilde = 2 * c

        deviations = []

        for k in range(M):
            np.random.seed()

            Delta = np.round(np.random.uniform(0, 1, len(c0))) * 2 - 1
            thetaPlus = X_current + (c * Delta)
            thetaMinus = X_current - (c * Delta)

            while (X_min > thetaPlus).any() or (thetaPlus > X_max).any() or (thetaMinus < X_min).any() or (
                thetaMinus > X_max).any():
                Delta = np.round(np.random.uniform(0, 1, len(c0))) * 2 - 1
                thetaPlus = X_current + (c * Delta)
                thetaMinus = X_current - (c * Delta)

            deviations.append((c * Delta).tolist())
            deviations.append((-c * Delta).tolist())

            Delta_tilde = np.round(np.random.uniform(0, 1, len(c0))) * 2 - 1
            thetaPlusPlus = thetaPlus + c_tilde * Delta_tilde
            thetaMinusPlus = thetaMinus + c_tilde * Delta_tilde

            while (thetaPlusPlus < X_min).any() or (thetaPlusPlus > X_max).any() or (thetaMinusPlus < X_min).any() or (
                thetaMinusPlus > X_max).any():
                Delta_tilde = np.round(np.random.uniform(0, 1, len(c0))) * 2 - 1
                thetaPlusPlus = thetaPlus + c_tilde * Delta_tilde
                thetaMinusPlus = thetaMinus + c_tilde * Delta_tilde

            deviations.append((c * Delta + c_tilde * Delta_tilde).tolist())
            deviations.append((-c * Delta + c_tilde * Delta_tilde).tolist())

        X_center = state.reset_index(drop=True).set_index(['Parameter'])[['Center']]
        xc = X_center.transpose().reset_index(drop=True)
        xc.columns.name = ""

        samples = pd.concat([xc] * (4 * M + 1)).reset_index(drop=True)
        # print(samples)

        dt = np.transpose(deviations)

        dynamic_state_by_param = dynamic_state.set_index('Parameter')
        for i, pname in enumerate(dynamic_state['Parameter']):
            Xcen = dynamic_state_by_param.loc[pname, 'Center']
            samples.loc[1:(4 * M + 1), pname] = Xcen + dt[i]

        return samples

    def end_condition(self):
        print("end_condition")
        # Stopping Criterion: good rsqared with small norm?
        # Return True to stop, False to continue
        logger.info('Continuing iterations ...')
        return False

    def get_final_samples(self):
        """
        Resample Stage:
        """
        print("get_final_samples")
        state_by_iteration = self.state.set_index('Iteration')
        last_iter = sorted(state_by_iteration.index.unique())[-1]

        X_Center = self._get_X_center(last_iter)
        xc = X_Center.to_frame().transpose().reset_index(drop=True)
        xc.columns.name = ""

        dtypes = {name: str(data.dtype) for name, data in xc.iteritems()}
        final_samples_NaN_to_Null = xc.where(~xc.isnull(), other=None)
        return {'final_samples': final_samples_NaN_to_Null.to_dict(orient='list'), 'final_samples_dtypes': dtypes}

    def prep_for_dict(self, df):
        # Needed for Windows compatibility
        # nulls = df.isnull()
        # if nulls.values.any():
        #    df[nulls] = None
        # return df.to_dict(orient='list')

        return df.where(~df.isnull(), other=None).to_dict(orient='list')

    def get_state(self):
        optimtool_state = dict(
            n_dimensions=self.n_dimensions,
            params=self.params,
            comps_per_iteration=self.comps_per_iteration,

            data=self.prep_for_dict(self.data),
            data_dtypes={name: str(data.dtype) for name, data in self.data.iteritems()},

            state=self.prep_for_dict(self.state),
            state_dtypes={name: str(data.dtype) for name, data in self.state.iteritems()}
        )
        return optimtool_state

    def set_state(self, state, iteration):
        self.n_dimensions = state['n_dimensions']
        self.params = state['params']  # NOTE: This line will override any updated user params passed to __init__
        self.comps_per_iteration = state['comps_per_iteration']

        data_dtypes = state['data_dtypes']
        self.data = pd.DataFrame.from_dict(state['data'], orient='columns')
        for c in self.data.columns:  # Argh
            self.data[c] = self.data[c].astype(data_dtypes[c])

        state_dtypes = state['state_dtypes']
        self.state = pd.DataFrame.from_dict(state['state'], orient='columns')
        for c in self.state.columns:  # Argh
            self.state[c] = self.state[c].astype(state_dtypes[c])

        self.need_resolve = True

    def get_param_names(self):
        return [p['Name'] for p in self.params]
