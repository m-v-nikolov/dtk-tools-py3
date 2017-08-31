import logging
import operator
import sys

import calibtool.algorithms.PBnB.m_intial_paramters_setting as par
from c_SubRegion import c_SubRegion
from calibtool.algorithms.NextPointAlgorithm import NextPointAlgorithm
from fun_PBnB_support_functions import *

logger = logging.getLogger('PBnB_application')
fh = logging.FileHandler('PBnB_running'+'-debug.log')
fh.setLevel(logging.INFO)
logger.addHandler(fh)

class OptimTool_PBnB(NextPointAlgorithm):
    def __init__(self, params, s_running_file_name, s_problem_type, constrain_sample_fn=lambda s: s,
                 f_delta=par.f_delta,
                 f_alpha=par.f_alpha,
                 i_k_b=par.i_k_b,
                 i_n_branching=par.i_n_branching,
                 i_c=par.i_c,
                 i_replication=par.i_replication,
                 i_stopping_max_k=par.i_stopping_max_k,
                 i_num_simulation_per_run=par.i_num_simulation_per_run,
                 ):
        #self.args = locals()  # Store inputs in case set_state is called later and we want to override with new (user) args

        self.constrain_sample_fn = constrain_sample_fn
        self.params = params

        self.f_delta = f_delta
        self.f_alpha = f_alpha
        self.i_n_branching = i_n_branching
        self.i_k_b = i_k_b
        self.i_c = i_c
        self.i_replication = i_replication
        self.i_stopping_max_k = i_stopping_max_k

        self.f_CI_u = 0
        self.f_CI_l = 0
        self.f_alpha_k = float(self.f_alpha) / self.i_n_branching
        self.i_c_k = i_c
        self.i_N_k = 0
        self.f_delta_k = f_delta
        self.i_N_elite_worst = 0
        self.i_R_elite_worst = 0
        self.i_R_k = i_replication
        self.df_testing_samples = pd.DataFrame()
        self.i_dimension = len(self.params)
        self.i_dimension_true = len([p for p in self.params if p['Dynamic'] is True]) #  delete the false dynamic dimension
        self.dict_n_branching_dim = {p['Name']: 0 for p in params if p['Dynamic'] is True}  # use for branching
        if max([p['Max']-p['Min'] for p in self.params]) < 100:
            self.f_epsilon = 0.25 * pow(max([p['Max']-p['Min'] for p in self.params]), self.i_dimension_true)  # can refer to the Hao's code: fun_diff(l_regionBound)
        else:
            self.f_epsilon = 0.15 * pow(max([p['Max']-p['Min'] for p in self.params]), self.i_dimension_true)
        self.f_epsilon_k = float(self.f_epsilon) / self.i_n_branching
        self.i_num_simulation_per_run = i_num_simulation_per_run
        self.s_running_file_name = s_running_file_name
        self.s_problem_type = s_problem_type
        # use for checking the iteration logic
        self.i_k = 1
        self.i_k_c = 1
        self.b_stopping_branchable = False
        self.s_stage = 'stage_1'

        # deal with the Dynamic true or false, fix the value of non-dynamic variables
        self.l_coordinate_upper = []
        self.l_coordinate_lower = []
        for p in self.params:
            if p['Dynamic'] is False:
                self.l_coordinate_upper.append(p['Guess'])
                self.l_coordinate_lower.append(p['Guess'])
            else:
                self.l_coordinate_upper.append(p['Max'])
                self.l_coordinate_lower.append(p['Min'])

        self.l_subr = []  # <-- list of subregion objects
        self.l_subr.append(c_SubRegion(self.l_coordinate_lower, self.l_coordinate_upper, self.params))  # <-- SIGMA_1={S}

    def get_samples_for_iteration(self, iteration):
        df_samples = self.fun_probability_branching_and_bound(iteration)
        if len(df_samples) >= self.i_num_simulation_per_run:
            print 'simulation per run sent to COMPS is exceeded the limitation ' + str(self.i_num_simulation_per_run)
            sys.exit()
        # return self.fun_generate_samples_from_df(df_samples[[p['Name'] for p in self.params]+['Run_Number']])
        return self.fun_generate_samples_from_df(df_samples[[p['Name'] for p in self.params]])

    def fun_generate_samples_from_df(self, df_samples):
        samples = []
        for sample in df_samples.itertuples():
            samples.append({k: v for k, v in zip(df_samples.columns.values, sample[1:])})
        return samples

    def fun_probability_branching_and_bound(self, iteration):
        logger.info('=======fun_probability_branching_and_bound=========')
        self.logging_saver(iteration)
        # step 1: Sample total c_k points in current subregions with updated replication number
        while self.i_k <= self.i_stopping_max_k:
            if self.s_stage == 'stage_1':
                logger.info('stage_1')


                self.i_N_k = int(self.i_c_k / sum(1 for j in self.l_subr if j.s_label == 'C' and j.b_activate is True))
                if self.s_problem_type is 'deterministic':
                    [self.l_subr, self.df_testing_samples] = fun_sample_points_generator_deterministic(self.l_subr, self.i_N_k, self.i_R_k, self.s_stage, [p['Name'] for p in self.params])
                elif self.s_problem_type is 'noise':
                    [self.l_subr, self.df_testing_samples] = fun_sample_points_generator_noise(self.l_subr, self.i_N_k, self.i_R_k, self.s_stage, [p['Name'] for p in self.params])
                self.s_stage = 'stage_2'
                if not self.df_testing_samples.empty:  # <-- call calibtool only if there is new sampling demand
                    return self.df_testing_samples

            # step 2: Order samples in each subregion and over all subregions byt estimated function values:
            if self.s_stage == 'stage_2':
                logger.info('stage_2')

                for c_subr in (c_subr for c_subr in self.l_subr if c_subr.s_label == 'C' and c_subr.b_activate is True and len(c_subr.pd_sample_record) > 0):
                    c_subr = copy.copy(fun_order_subregion(c_subr))

                # resampling
                self.i_R_k = fun_replication_update(self.l_subr, self.i_R_k, self.f_alpha_k)
                if self.s_problem_type is 'deterministic':
                    [self.l_subr, self.df_testing_samples] = fun_sample_points_generator_deterministic(self.l_subr, self.i_N_k,
                                                                                     self.i_R_k, self.s_stage, [p['Name'] for p in self.params])
                elif self.s_problem_type is 'noise':
                    [self.l_subr, self.df_testing_samples] = fun_sample_points_generator_noise(self.l_subr, self.i_N_k, self.i_R_k, self.s_stage, [p['Name'] for p in self.params])
                self.s_stage = 'stage_3'
                if not self.df_testing_samples.empty: # <-- call calibtool only if there is new sampling demand
                    return self.df_testing_samples

            if self.s_stage == 'stage_3':
                logger.info('stage_3')

                # reorder
                for c_subr in (c_subr for c_subr in self.l_subr if c_subr.s_label == 'C' and c_subr.b_activate is True and len(c_subr.pd_sample_record) > 0):
                    c_subr = copy.copy(fun_order_subregion(c_subr))

        # step 3: Build CI of quantile
                pd_order_z = fun_order_region(self.l_subr)
                [self.f_CI_u, self.f_CI_l] = fun_CI_builder(self.l_subr, pd_order_z, self.f_delta_k, self.f_alpha_k, self.f_epsilon)
                self.s_stage = 'stage_4-1'

        # step 4: Find the elite and worst subregions, and further sample with updated replications
            if self.s_stage == 'stage_4-1' or self.s_stage == 'stage_4-2' or self.s_stage == 'stage_5':
                while (self.i_k_c < self.i_k_b or self.i_k == 1) and self.i_k <= self.i_stopping_max_k:  # (3)
                    logger.info('elite and worst inner loop')
                    if self.s_stage == 'stage_4-1':
                        logger.info('stage_4-1')
                        self.l_subr = fun_elite_indicator(self.l_subr, self.f_CI_l)
                        self.l_subr = fun_worst_indicator(self.l_subr, self.f_CI_u)


                        self.i_N_elite_worst = int(np.ceil(np.log(self.f_alpha_k) /
                                                           np.log(1. - (self.f_epsilon / self.l_subr[0].f_volume))))  # <-- number of sampling points for elite and worst subregions
                        if self.s_problem_type is 'deterministic':
                            [self.l_subr, self.df_testing_samples] = fun_sample_points_generator_deterministic(self.l_subr, self.i_N_elite_worst, self.i_R_k, self.s_stage, [p['Name'] for p in self.params])
                        elif self.s_problem_type is 'noise':
                            [self.l_subr, self.df_testing_samples] = fun_sample_points_generator_noise(self.l_subr, self.i_N_k, self.i_R_k, self.s_stage, [p['Name'] for p in self.params])
                        self.s_stage = 'stage_4-2'
                        if not self.df_testing_samples.empty:  # <-- call calibtool only if there is new sampling demand
                            return self.df_testing_samples
                    elif self.s_stage == 'stage_4-2':
                        logger.info('stage_4-2')
                        # reorder
                        for i in (i for i in self.l_subr if i.s_label == 'C' and len(i.pd_sample_record) > 0):
                            i = fun_order_subregion(i)

                        # perform R_k^n-R_k
                        self.i_R_elite_worst = fun_replication_update(self.l_subr, self.i_R_k, self.f_alpha_k)  # <-- number of replication for all sampling points in elite and worst regions
                        if self.s_problem_type is 'deterministic':
                            [self.l_subr, self.df_testing_samples] = fun_sample_points_generator_deterministic(self.l_subr, self.i_N_elite_worst, self.i_R_elite_worst, self.s_stage, [p['Name'] for p in self.params])
                        elif self.s_problem_type is 'noise':
                            [self.l_subr, self.df_testing_samples] = fun_sample_points_generator_noise(self.l_subr, self.i_N_k, self.i_R_k, self.s_stage, [p['Name'] for p in self.params])
                        self.s_stage = 'stage_5'
                        if not self.df_testing_samples.empty:  # <-- call calibtool only if there is new sampling demand
                            return self.df_testing_samples

                # step 5: Maintain, prune, and branch
                    elif self.s_stage == 'stage_5':
                        logger.info('stage_5')
                        self.l_subr = fun_pruning_indicator(self.l_subr, self.f_CI_u)
                        self.l_subr = fun_maintaining_indicator(self.l_subr, self.f_CI_l)
                        # need to update the maintained set and the pruned set and reset all the indicator and label
                        self.f_delta_k = fun_quantile_update(self.l_subr, self.f_delta_k)

                        self.l_subr = fun_pruning_labeler(self.l_subr)
                        self.l_subr = fun_maintaining_labeler(self.l_subr)
                        if any(c_subr.s_label == 'M' for c_subr in self.l_subr):
                            fun_plot2D(self.l_subr, self.l_subr[0].l_coordinate_lower, self.l_subr[0].l_coordinate_upper, self.params, self.i_k, self.s_running_file_name, iteration)
                            sys.exit()
                        # determine the next step
                        self.b_stopping_branchable = all(i.b_branchable is False for i in (i for i in self.l_subr if i.b_activate is True)) or all(i.s_label != 'C' for i in (i for i in self.l_subr if i.b_activate is True))  # any subregion is branchable
                        if self.b_stopping_branchable is True:  # (1)
                            self.print_results_for_iteration()
                        else:  # (2) and (3)
                            # beginning of branching-------------------------------

                            # 1: the longest dimension
                            """
                            l_temp_new_branching_subr = []
                            for c_subr in (c_subr for c_subr in self.l_subr if
                                           c_subr.s_label == 'C' and c_subr.b_activate is True and c_subr.b_branchable is True):
                                my_list = (np.array(c_subr.l_coordinate_upper) - np.array(c_subr.l_coordinate_lower)).tolist()
                                f_max_value = max(my_list)
                                i_max_index = my_list.index(f_max_value)
                                s_branching_dim = [p['Name'] for p in self.params][i_max_index]

                                c_subr.b_activate = False  # deactivate the original subregion
                                l_temp_new_branching_subr += fun_reg_branching(c_subr, self.i_n_branching, self.params,
                                                                               s_branching_dim)
                            """
                            
                            # 2: alternative: choose the dimension having the minimum branching

                            s_branching_dim = min(self.dict_n_branching_dim, key=self.dict_n_branching_dim.get)
                            if self.i_k == 1:
                                s_branching_dim = 'funestus_scale'
                            self.dict_n_branching_dim[s_branching_dim] += 1
                            l_temp_new_branching_subr = []
                            for c_subr in (c_subr for c_subr in self.l_subr if c_subr.s_label == 'C' and c_subr.b_activate is True and c_subr.b_branchable is True):

                                c_subr.b_activate = False  # deactivate the original subregion
                                l_temp_new_branching_subr += fun_reg_branching(c_subr, self.i_n_branching, self.params, s_branching_dim)

                            self.l_subr += l_temp_new_branching_subr  # append the branching subregions to the list
                            # the following index the subregions for get and set results
                            index_number = 0
                            for c_subr in self.l_subr:
                                c_subr.i_index = index_number
                                index_number += 1

                            # end of branching-------------------------------
                            if all(i.b_maintaining_indicator is False for i in
                               (i for i in self.l_subr if i.b_activate is True)) and all(i.b_pruning_indicator is False for i in
                                                                                        (i for i in self.l_subr if i.b_activate is True)):
                                self.i_k_c += 1
                            else:
                                self.i_k_c = 0
                            # reset pruning and maintaining updaters
                            for i in self.l_subr:
                                i.b_maintaining_indicator = False
                                i.b_pruning_indicator = False
                            # update others parameters
                            self.f_alpha_k = float(self.f_alpha) / pow(self.i_n_branching, self.i_k)
                            self.f_epsilon_k = float(self.f_epsilon) / pow(self.i_n_branching, self.i_k)
                            self.i_c_k = self.i_c * self.i_k
                            self.i_k += 1
                            self.s_stage = 'stage_4-1'
                            if self.i_k_c >= self.i_k_b:  # (2)
                                self.i_k_c = 1
                                self.s_stage = 'stage_1'
                                break
                        # the following save l_subr
                    #with open("test.dat", "wb") as f:
                        #pickle.dump(self.l_subr, f)
                    # with open("test.dat", "rb") as f:
                    # print pickle.load(f)

        self.print_results_for_iteration()
        #plot2D(l_subr, l_subr[0].l_coordinate_lower, l_subr[0].l_coordinate_upper, 'final')

    def logging_saver(self, iteration):
        logger.info('================begin: logging_saver================')
        logger.info('iteration:' + str(iteration))
        logger.info('self.s_stage:'+str(self.s_stage))
        logger.info('self.self.i_k:' + str(self.i_k))
        logger.info('self.i_k_c:' + str(self.i_k_c))
        for i in self.l_subr:
            logger.info('l_coordinate_lower: ' + str(i.l_coordinate_lower))
            logger.info('l_coordinate_upper: ' + str(i.l_coordinate_upper))
            logger.info('activate: ' + str(i.b_activate))
            logger.info('label: ' + str(i.s_label))
            logger.info('worst: ' + str(i.b_worst))
            logger.info('elite: ' + str(i.b_elite))
            logger.info('i_min_sample: ' + str(i.i_min_sample))
            logger.info('i_max_sample: ' + str(i.i_max_sample))
            logger.info('f_min_diff_sample_mean: ' + str(i.f_min_diff_sample_mean))
            logger.info('f_max_var: ' + str(i.f_max_var))
            logger.info('pd_sample_record: ')
            logger.info(i.pd_sample_record)
        logger.info('================end: logging_saver================')

    def print_results_for_iteration(self):
        if self.b_stopping_branchable is True:
            print ('no branchable subregions')
            for i in (i for i in self.l_subr if i.b_activate is True):
                print ('l_coordinate_lower: ' + str(i.l_coordinate_lower))
                print ('l_coordinate_upper: ' + str(i.l_coordinate_upper))
                print ('activate: ' + str(i.b_activate))
                print ('label: ' + str(i.s_label))
                print ('worst: ' + str(i.b_worst))
                print ('elite: ' + str(i.b_elite))
        else:
            print ('reach the maximum number of iteration')
            print ('[f_CI_u,f_CI_l]: ' + str([self.f_CI_u, self.f_CI_l]))
            for i in (i for i in self.l_subr if i.b_activate is True and i.s_label == 'P'):
                print ('l_coordinate_lower: ' + str(i.l_coordinate_lower))
                print ('l_coordinate_upper: ' + str(i.l_coordinate_upper))
                print ('activate: ' + str(i.b_activate))
                print ('label: ' + str(i.s_label))
                print ('worst: ' + str(i.b_worst))
                print ('elite: ' + str(i.b_elite))
                print ('i_min_sample: ' + str(i.i_min_sample))
                print ('i_max_sample: ' + str(i.i_max_sample))
                print ('f_min_diff_sample_mean: ' + str(i.f_min_diff_sample_mean))
                print ('f_max_var: ' + str(i.f_max_var))
                # print ('pd_sample_record: ')
                # print (i.pd_sample_record)
                print ('')
            for i in (i for i in self.l_subr if i.b_activate is True and i.s_label == 'M'):
                print ('l_coordinate_lower: ' + str(i.l_coordinate_lower))
                print ('l_coordinate_upper: ' + str(i.l_coordinate_upper))
                print ('activate: ' + str(i.b_activate))
                print ('label: ' + str(i.s_label))
                print ('worst: ' + str(i.b_worst))
                print ('elite: ' + str(i.b_elite))
                print ('i_min_sample: ' + str(i.i_min_sample))
                print ('i_max_sample: ' + str(i.i_max_sample))
                print ('f_min_diff_sample_mean: ' + str(i.f_min_diff_sample_mean))
                print ('f_max_var: ' + str(i.f_max_var))
                # print ('pd_sample_record: ')
                # print (i.pd_sample_record)
                print ('')
                # print ('pd_sample_record: ')
                # print (i.pd_sample_record.loc[0])
                # print ('pd_sample_record: ')
                # print (i.pd_sample_record.loc[len(i.pd_sample_record)])

    def set_results_for_iteration(self, iteration, results):
        logger.info('================begin: set_results_for_iteration================')
        # self.df_testing_samples['result'] = pd.Series(results[results.columns[0]], index=self.df_testing_samples.index)
        if self.s_problem_type is 'deterministic':
            self.df_testing_samples['result'] = pd.Series([[p] for p in results[results.columns[0]]], index=self.df_testing_samples.index) # negative p is because we would like to minimize -negative likelihood()= maximum likelihood
        elif self.s_problem_type is 'noise':
            self.df_testing_samples['result'] = pd.Series([p for p in results[results.columns[0]]], index=self.df_testing_samples.index)
        logger.info('result')
        logger.info(results)
        logger.info('self.df_testing_samples')
        logger.info(self.df_testing_samples)
        self.logging_saver(iteration)

        if iteration == 0:
            os.makedirs(self.s_running_file_name+'/All_region_sampling_record/')
        if self.s_problem_type is 'deterministic':
            self.l_subr = fun_results_organizer_deterministic(self.l_subr, self.df_testing_samples, self.params)  # <-- Update the self.l_subr based on df_testing_samples
        elif self.s_problem_type is 'noise':
            self.l_subr = fun_results_organizer_noise(self.l_subr, self.df_testing_samples, self.i_N_k, self.i_N_elite_worst, self.s_stage, self.params)
        for i in range(0, len(self.l_subr)):
            name = 'l_subr['+str(i)+'].pd_sample_record.csv'
            self.l_subr[i].pd_sample_record.to_csv(self.s_running_file_name+'/All_region_sampling_record/'+name, index=True)
        # fun_plot2D(self.l_subr, self.l_subr[0].l_coordinate_lower, self.l_subr[0].l_coordinate_upper, self.params, str(self.i_k))
        with open(self.s_running_file_name+'/All_region_sampling_record/'+'l_subr_all_simulations_iteration_' + str(self.i_k) + '.dat', "wb") as f:
            pickle.dump(self.l_subr, f)

        logger.info('================end: set_results_for_iteration================')

    def get_state(self):
        optimtool_state = dict(
            params=self.params,
            f_delta=self.f_delta,
            f_alpha=self.f_alpha,
            i_n_branching=self.i_n_branching,
            i_k_b=self.i_k_b,
            i_c_k=self.i_c,
            i_c=self.i_c,
            i_replication=self.i_replication,
            i_stopping_max_k=self.i_stopping_max_k,
            b_stopping_branchable=self.b_stopping_branchable,

            i_k=self.i_k,
            i_k_c=self.i_k_c,
            s_stage=self.s_stage,
            f_CI_u=self.f_CI_u,
            f_CI_l=self.f_CI_l,
            f_alpha_k=self.f_alpha_k,
            f_epsilon=self.f_epsilon,
            i_N_k=self.i_N_k,
            f_delta_k=self.f_delta_k,
            i_N_elite_worst=self.i_N_elite_worst,
            i_R_elite_worst=self.i_R_elite_worst,
            i_R_k=self.i_R_k,
            i_dimension=self.i_dimension,
            i_dimension_true=self.i_dimension_true,
            dict_n_branching_dim=self.dict_n_branching_dim,
            df_testing_samples=self.df_testing_samples.where(~self.df_testing_samples.isnull(), other=None).to_dict(orient='list')
        )
        optimtool_state_l_subr = {}
        for c_subr in self.l_subr:
            s_c_subr_name = str(c_subr.l_coordinate_lower)+','+str(c_subr.l_coordinate_upper)
            optimtool_state_c_subr = {s_c_subr_name: {
                    's_label': c_subr.s_label,
                    'i_index': c_subr.i_index,
                    'b_activate': c_subr.b_activate,
                    'b_branchable': c_subr.b_branchable,
                    'b_elite': c_subr.b_elite,
                    'b_worst': c_subr.b_worst,
                    'b_maintaining_indicator': c_subr.b_maintaining_indicator,
                    'b_pruning_indicator': c_subr.b_pruning_indicator,
                    'l_coordinate_lower': c_subr.l_coordinate_lower,
                    'l_coordinate_upper': c_subr.l_coordinate_upper,
                    'f_volume': c_subr.f_volume,
                    'i_min_sample': c_subr.i_min_sample,
                    'i_max_sample': c_subr.i_max_sample,
                    'f_min_diff_sample_mean': c_subr.f_min_diff_sample_mean,
                    'f_max_var': c_subr.f_max_var,
                    'pd_sample_record': c_subr.pd_sample_record.where(~c_subr.pd_sample_record.isnull(), other=None).to_dict(orient='list')}}
            optimtool_state_l_subr.update(optimtool_state_c_subr)
        optimtool_state_l_subr = {'l_subr': optimtool_state_l_subr}
        optimtool_state.update(optimtool_state_l_subr)
        return optimtool_state

    def set_state(self, state, iteration):
        self.params = state['params']
        self.f_delta = state['f_delta']
        self.f_alpha = state['f_alpha']
        self.i_n_branching = state['i_n_branching']
        self.i_k_b = state['i_k_b']
        self.i_c_k = state['i_c_k']
        self.i_c = state['i_c']
        self.i_replication = state['i_replication']
        self.i_stopping_max_k = state['i_stopping_max_k']
        self.b_stopping_branchable = state['b_stopping_branchable']

        self.i_k = state['i_k']
        self.i_k_c = state['i_k_c']

        self.s_stage = state['s_stage']
        self.f_CI_u = state['f_CI_u']
        self.f_CI_l = state['f_CI_l']
        self.f_alpha_k = state['f_alpha_k']
        self.f_epsilon = state['f_epsilon']
        self.i_N_k = state['i_N_k']
        self.f_delta_k = state['f_delta_k']
        self.i_N_elite_worst = state['i_N_elite_worst']
        self.i_R_elite_worst = state['i_R_elite_worst']
        self.i_R_k = state['i_R_k']
        self.df_testing_samples = pd.DataFrame.from_dict(state['df_testing_samples'], orient='columns')
        self.df_testing_samples['replication'].astype(int)
        self.i_dimension = state['i_dimension']
        self.i_dimension_true = state['i_dimension_true']
        self.dict_n_branching_dim = state['dict_n_branching_dim']
        self.l_subr = []  # <-- list of subregion objects

        for c_subr in state['l_subr']:
            c_subr_set = c_SubRegion(state['l_subr'][c_subr]['l_coordinate_lower'], state['l_subr'][c_subr]['l_coordinate_upper'], self.params)
            c_subr_set.i_index = state['l_subr'][c_subr]['i_index']
            c_subr_set.s_label = state['l_subr'][c_subr]['s_label']
            c_subr_set.b_activate = state['l_subr'][c_subr]['b_activate']
            c_subr_set.b_branchable = state['l_subr'][c_subr]['b_branchable']
            c_subr_set.b_elite = state['l_subr'][c_subr]['b_elite']
            c_subr_set.b_worst = state['l_subr'][c_subr]['b_worst']
            c_subr_set.b_maintaining_indicator = state['l_subr'][c_subr]['b_maintaining_indicator']
            c_subr_set.b_pruning_indicator = state['l_subr'][c_subr]['b_pruning_indicator']
            c_subr_set.f_volume = state['l_subr'][c_subr]['f_volume']
            c_subr_set.i_min_sample = state['l_subr'][c_subr]['i_min_sample']
            c_subr_set.i_max_sample = state['l_subr'][c_subr]['i_max_sample']
            c_subr_set.f_min_diff_sample_mean = state['l_subr'][c_subr]['f_min_diff_sample_mean']
            c_subr_set.f_max_var = state['l_subr'][c_subr]['f_max_var']
            c_subr_set.pd_sample_record = pd.DataFrame.from_dict(state['l_subr'][c_subr]['pd_sample_record'], orient='columns')
            c_subr_set.pd_sample_record['rep'].astype(int)
            self.l_subr.append(c_subr_set)
        self.l_subr.sort(key=operator.attrgetter('i_index'))  # dinc->list and sorting

    def end_condition(self):
        for c_subr in self.l_subr:
            if c_subr.s_label == 'M':
                return True


    def get_results_to_cache(self, results):
        results['total'] = results.sum(axis=1)
        return results.to_dict(orient='list')

    def get_final_samples(self):
        # print the best sample
        return {'best_sample': min([p.i_min_sample for p in self.l_subr])}

    def update_summary_table(self, iteration_state, previous_results):
        """
        copy from NExtPointAlgorithm,  output: all_results, summary_table
        """
        results_df = pd.DataFrame.from_dict(iteration_state.results, orient='columns')
        results_df.index.name = 'sample'

        params_df = pd.DataFrame(iteration_state.samples_for_this_iteration)

        df = pd.concat((results_df, params_df), axis=1)
        df['iteration'] = iteration_state.iteration

        previous_results = pd.concat((previous_results, df)).sort_values(by='total', ascending=False)
        return previous_results, previous_results[['iteration', 'total']].head(10)

    def get_param_names(self):
        return [p['Name'] for p in self.params]

    def cleanup(self):
        pass
