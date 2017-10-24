import copy
import math

import numpy as np
import pandas as pd
import scipy.stats
from scipy.stats import binom

from .c_SubRegion import c_SubRegion

"""
This function uniformly sampling i_n_samp sample points with i_n_rep replication in the subregions c_subregion and generate the df that used to sent to calibtool
input:
    i_n_samp: # sampling needed in the subregion
    i_n_rep: # replication needed in the subregion
    c_subr:examing subregion
outout
    l_subr
    df_testing_samples
"""
# TODO: plotter that can choose any two dimension and fix the value of other dimensions

def fun_sample_points_generator_deterministic(l_subr, i_n_sampling, i_n_rep, s_stage, l_para):
    l_column = ['l_coordinate_lower', 'l_coordinate_upper'] + l_para + ['replication']
    df_testing_samples = pd.DataFrame([], columns=l_column)  # the dataframe contains the sampling point sent to calibtool
    df_testing_samples['replication'].astype(int)
    l_sampling_subregions = []
    if s_stage == 'stage_1':
        l_sampling_subregions = [c_subr for c_subr in l_subr if c_subr.s_label == 'C' and c_subr.b_activate is True]
    elif s_stage == 'stage_2':
        l_sampling_subregions = [c_subr for c_subr in l_subr if (c_subr.s_label == 'C' and c_subr.b_activate is True and len(c_subr.pd_sample_record) > 0)]
    elif s_stage == 'stage_4-1':
        l_sampling_subregions = [c_subr for c_subr in l_subr if (c_subr.s_label == 'C' and c_subr.b_activate is True and (c_subr.b_worst is True or c_subr.b_elite is True))]
    elif s_stage == 'stage_4-2':
        l_sampling_subregions = [c_subr for c_subr in l_subr if (c_subr.s_label == 'C' and c_subr.b_activate is True and (c_subr.b_worst is True or c_subr.b_elite is True))]
    if not l_sampling_subregions:
        return [l_subr, pd.DataFrame()]
    for c_subr in l_sampling_subregions:
        c_subr.pd_sample_record = c_subr.pd_sample_record.sort_values(by="mean",
                                                                      ascending=True)  # sort before start
        c_subr.pd_sample_record = c_subr.pd_sample_record.reset_index(drop=True)  # reindex before start
        if len(c_subr.pd_sample_record) >= i_n_sampling:  # if has enough number of sampling points
            for i in (i for i in range(0, len(c_subr.pd_sample_record)) if
                      c_subr.pd_sample_record.loc[i, 'rep'] < i_n_rep):  # check enough # reps or not, i is index
                #df_testing_samples.append(pd.DataFrame([[c_subr.l_coordinate_lower] + [c_subr.l_coordinate_upper] + [c_subr.pd_sample_record.loc[i, p] for p in l_para] + [i_n_rep - int(c_subr.pd_sample_record.loc[i, '# rep'])]], columns=l_column))
                l_vals = [c_subr.l_coordinate_lower] + [c_subr.l_coordinate_upper] + [c_subr.pd_sample_record.loc[i, p] for p in l_para] + [i_n_rep - int(c_subr.pd_sample_record.loc[i, 'rep'])]
                df_testing_samples = df_testing_samples.append(dict(zip(l_column, l_vals)), ignore_index=True)

        else:  # if has not enough sampling points and replication
            if len(c_subr.pd_sample_record) >= 1:  # if already has sample points, first deal with them
                for i in (i for i in range(0, len(c_subr.pd_sample_record)) if c_subr.pd_sample_record.loc[i, 'rep'] < i_n_rep):  # check enough # reps or not for existing old sampling points
                    #df_testing_samples.append(pd.DataFrame([[c_subr.l_coordinate_lower] + [c_subr.l_coordinate_upper] + [c_subr.pd_sample_record.loc[i, p] for p in l_para] + [i_n_rep - int(c_subr.pd_sample_record.loc[i, '# rep'])]], columns=l_column))
                    l_vals = [c_subr.l_coordinate_lower] + [c_subr.l_coordinate_upper] + [c_subr.pd_sample_record.loc[i, p] for p in l_para] + [i_n_rep - int(c_subr.pd_sample_record.loc[i, 'rep'])]
                    df_testing_samples = df_testing_samples.append(dict(zip(l_column, l_vals)), ignore_index=True)
            i_ini_length = len(c_subr.pd_sample_record)  # number of sampling point so far in this subregion
            for i in range(i_ini_length, i_n_sampling):  # create new rows for new sampling points
                c_subr.pd_sample_record.loc[i] = [1 for n in range(len(c_subr.pd_sample_record.columns))]
                c_subr.pd_sample_record.loc[i, 'rep'] = 0

            index = [x for x in range(i_ini_length, i_n_sampling)]
            for i in range(0, len(l_para)):  # create new sampling point and add to dataframe
                a_new_sample = np.random.uniform(low=c_subr.l_coordinate_lower[i],
                                                 high=c_subr.l_coordinate_upper[i],
                                                 size=i_n_sampling - i_ini_length)  # generate only for one dim

                c_subr.pd_sample_record.loc[i_ini_length:i_n_sampling - 1, l_para[i]] = pd.Series(
                    a_new_sample.tolist(), index)
                c_subr.pd_sample_record.loc[index, l_para[i]] = pd.Series(a_new_sample.tolist(), index)
            c_subr.pd_sample_record.loc[index, 'mean'] = 0
            c_subr.pd_sample_record.loc[index, 'var'] = 0
            c_subr.pd_sample_record.loc[index, 'SST'] = 0
            for i in range(i_ini_length, i_n_sampling):  # put the new generate sample points in df_samples
                l_vals = [c_subr.l_coordinate_lower]+[c_subr.l_coordinate_upper]+[c_subr.pd_sample_record.loc[i, p] for p in l_para] + [i_n_rep]
                df_testing_samples = df_testing_samples.append(dict(zip(l_column, l_vals)), ignore_index=True)
    return [l_subr, df_testing_samples]


def fun_sample_points_generator_noise (l_subr, i_n_sampling, i_n_rep, s_stage, l_para):
    l_column = ['l_coordinate_lower', 'l_coordinate_upper'] + l_para
    df_testing_samples = pd.DataFrame([], columns=l_column)

    if s_stage == 'stage_1':
        l_sampling_subregions = [c_subr for c_subr in l_subr if c_subr.s_label == 'C' and c_subr.b_activate is True]
    elif s_stage == 'stage_2':
        l_sampling_subregions = [c_subr for c_subr in l_subr if c_subr.s_label == 'C' and c_subr.b_activate is True and len(c_subr.pd_sample_record) > 0]
    elif s_stage == 'stage_4-1':
        l_sampling_subregions = [c_subr for c_subr in l_subr if c_subr.s_label == 'C' and c_subr.b_activate is True and (c_subr.b_worst is True or c_subr.b_elite is True)]
    else:
        l_sampling_subregions = [c_subr for c_subr in l_subr if c_subr.s_label == 'C' and c_subr.b_activate is True and (c_subr.b_worst is True or c_subr.b_elite is True)]

    for c_subr in l_sampling_subregions:
        c_subr.pd_sample_record = c_subr.pd_sample_record.sort_values(by="mean",
                                                                      ascending=True)  # sort before start
        c_subr.pd_sample_record = c_subr.pd_sample_record.reset_index(drop=True)  # reindex before start

        if len(c_subr.pd_sample_record) >= i_n_sampling:  # if has enough number of sampling points
            for i in (i for i in range(0, len(c_subr.pd_sample_record)) if
                      c_subr.pd_sample_record.loc[i, 'rep'] < i_n_rep):  # check enough # reps or not, i is index
                #df_testing_samples.append(pd.DataFrame([[c_subr.l_coordinate_lower] + [c_subr.l_coordinate_upper] + [c_subr.pd_sample_record.loc[i, p] for p in l_para] + [i_n_rep - int(c_subr.pd_sample_record.loc[i, '# rep'])]], columns=l_column))
                l_vals = [c_subr.l_coordinate_lower] + [c_subr.l_coordinate_upper] + [c_subr.pd_sample_record.loc[i, p] for p in l_para]
                for j in range(0, i_n_rep - int(c_subr.pd_sample_record.loc[i, 'rep'])):
                    df_testing_samples = df_testing_samples.append(dict(zip(l_column, l_vals)), ignore_index=True)

        else:  # if has not enough sampling points and replication
            if len(c_subr.pd_sample_record) >= 1:  # if already has sample points, first deal with them
                for i in (i for i in range(0, len(c_subr.pd_sample_record)) if c_subr.pd_sample_record.loc[i, 'rep'] < i_n_rep):  # check enough # reps or not for existing old sampling points
                    #df_testing_samples.append(pd.DataFrame([[c_subr.l_coordinate_lower] + [c_subr.l_coordinate_upper] + [c_subr.pd_sample_record.loc[i, p] for p in l_para] + [i_n_rep - int(c_subr.pd_sample_record.loc[i, '# rep'])]], columns=l_column))
                    l_vals = [c_subr.l_coordinate_lower] + [c_subr.l_coordinate_upper] + [c_subr.pd_sample_record.loc[i, p] for p in l_para]
                    for j in range(0,[i_n_rep - int(c_subr.pd_sample_record.loc[i, 'rep'])]):
                        df_testing_samples = df_testing_samples.append(dict(zip(l_column, l_vals)), ignore_index=True)
            i_ini_length = len(c_subr.pd_sample_record)  # number of sampling point so far in this subregion
            for i in range(i_ini_length, i_n_sampling):  # create new rows for new sampling points
                c_subr.pd_sample_record.loc[i] = [1 for n in range(len(c_subr.pd_sample_record.columns))]

            index = [x for x in range(i_ini_length, i_n_sampling)]
            for i in range(0, len(l_para)):  # create new sampling point and add to dataframe
                a_new_sample = np.random.uniform(low=c_subr.l_coordinate_lower[i],
                                                 high=c_subr.l_coordinate_upper[i],
                                                 size=i_n_sampling - i_ini_length)  # generate only for one dim

                c_subr.pd_sample_record.loc[i_ini_length:i_n_sampling - 1, l_para[i]] = pd.Series(
                    a_new_sample.tolist(), index)
                c_subr.pd_sample_record.loc[index, l_para[i]] = pd.Series(a_new_sample.tolist(), index)
            c_subr.pd_sample_record.loc[index, 'mean'] = 0
            c_subr.pd_sample_record.loc[index, 'var'] = 0
            c_subr.pd_sample_record.loc[index, 'SST'] = 0
            c_subr.pd_sample_record.loc[index, 'rep'] = 0
            for i in range(i_ini_length, i_n_sampling):  # put the new generate sample points in df_samples
                l_vals = [c_subr.l_coordinate_lower]+[c_subr.l_coordinate_upper]+[c_subr.pd_sample_record.loc[i, p] for p in l_para] + [i_n_rep]
                for j in range(0, i_n_rep):
                    df_testing_samples = df_testing_samples.append(dict(zip(l_column, l_vals)), ignore_index=True)
    return [l_subr, df_testing_samples]

def turn_to_power(list, power):
    return [number**power for number in list]


def fun_results_organizer_deterministic(l_subr, df_testing_samples, params):
    # df_testing_samples: ['l_coordinate_lower', 'l_coordinate_upper'] + l_para + ['replication'] + ['result']
    df_testing_samples = df_testing_samples.reset_index(drop=True)
    for c_subr in [c_subr for c_subr in l_subr if c_subr.s_label == 'C' and c_subr.b_activate is True]:
        df_testing_samples_s_subr = pd.DataFrame([],
                                                 columns=[p['Name'] for p in params] + ['rep'] + ['mean'] + ['var'] + [
                                                     'SST'])
        df_testing_samples_s_subr['rep'].astype(int)
        df_testing_samples_s_subr['mean'].astype(float)
        df_testing_samples_s_subr['var'].astype(float)
        df_testing_samples_s_subr['SST'].astype(float)
        c_subr.pd_sample_record.drop(c_subr.pd_sample_record[c_subr.pd_sample_record.rep == 0].index, inplace=True)
        df_testing_samples['l_coordinate_lower'] = df_testing_samples['l_coordinate_lower'].astype(str)
        df_testing_samples['l_coordinate_upper'] = df_testing_samples['l_coordinate_upper'].astype(str)
        df_testing_samples_s_subr[[p['Name'] for p in params]+['mean']] = df_testing_samples[(df_testing_samples['l_coordinate_lower'] == str(c_subr.l_coordinate_lower)) & (df_testing_samples['l_coordinate_upper'] == str(c_subr.l_coordinate_upper))][[p['Name'] for p in params]+['result']]
        df_testing_samples_s_subr = df_testing_samples_s_subr.reset_index(drop=True)
        if len(df_testing_samples_s_subr) > 0:
            for i in range(0, len(df_testing_samples_s_subr)):
                df_testing_samples_s_subr.loc[i, 'mean'] = df_testing_samples_s_subr.loc[i, 'mean'][0]
            df_testing_samples_s_subr['rep'] = 1
            df_testing_samples_s_subr['var'] = 0
            df_testing_samples_s_subr['SST'] = df_testing_samples_s_subr.apply(lambda row: (row['mean'] * row['mean']), axis=1)
            c_subr.pd_sample_record = pd.concat([c_subr.pd_sample_record, df_testing_samples_s_subr])
        # the following update i_min_sample, i_max_sample, f_min_diff_sample_mean, and f_max_var
        c_subr.pd_sample_record = c_subr.pd_sample_record.sort_values(by="mean", ascending=True)
        c_subr.pd_sample_record = c_subr.pd_sample_record.reset_index(drop=True)  # reindex the sorted df
        if len(c_subr.pd_sample_record) > 0:
            c_subr.i_min_sample = c_subr.pd_sample_record.loc[0, 'mean']
            c_subr.i_max_sample = c_subr.pd_sample_record.loc[len(c_subr.pd_sample_record) - 1, 'mean']
        c_subr.f_min_diff_sample_mean = min(
            c_subr.pd_sample_record['mean'].shift(-1) - c_subr.pd_sample_record['mean'])
        c_subr.f_max_var = max(c_subr.pd_sample_record.loc[:, 'var'])
    return l_subr


def fun_results_organizer_noise(l_subr, df_testing_samples, i_n_k, i_n_elite_worst, s_stage, params):
    l_params = [p['Name'] for p in params]
    if s_stage in ['stage_1', 'stage_2', 'stage_4-1']:
        i_n = i_n_k
    else:
        i_n = i_n_elite_worst
    df_testing_samples = df_testing_samples.reset_index(drop=True)

    df_testing_samples['square_result'] = np.power(df_testing_samples['result'], 2)
    df_testing_samples_grouped = df_testing_samples.groupby(l_params).agg({'result': [np.mean, np.var, np.sum, 'count'], 'square_result': 'sum'}).reset_index()
    df_testing_samples_grouped.columns = df_testing_samples_grouped.columns.droplevel(level=0)
    df_testing_samples_grouped.columns = l_params + ['new_data_mean', 'new_data_var', 'new_data_sum', 'new_data_rep', 'new_data_SST']


    for c_subr in [c_subr for c_subr in l_subr if c_subr.s_label == 'C' and c_subr.b_activate is True]:
        c_subr.pd_sample_record = pd.merge(c_subr.pd_sample_record, df_testing_samples_grouped, on=l_params)
        c_subr.pd_sample_record['new_data_mean'].astype(float)
        c_subr.pd_sample_record['new_data_var'].astype(float)
        c_subr.pd_sample_record['new_data_sum'].astype(float)
        c_subr.pd_sample_record['new_data_rep'].astype(int)
        c_subr.pd_sample_record['new_data_SST'].astype(float)

        c_subr.pd_sample_record['mean'] = copy.copy(c_subr.pd_sample_record.apply(lambda row: float(row['rep']* row['mean'] + row['new_data_rep'] * row['new_data_mean']) / i_n, axis=1))
        c_subr.pd_sample_record['SST'] = copy.copy(c_subr.pd_sample_record.apply(lambda row: row['SST']+row['new_data_SST'], axis=1))
        c_subr.pd_sample_record['var'] = copy.copy(c_subr.pd_sample_record.apply(lambda row: float(row['SST'] - i_n * pow(row['mean'], 2)) / (i_n - 1), axis=1))
        c_subr.pd_sample_record['rep'] = copy.copy(i_n)
        c_subr.pd_sample_record.drop(['new_data_mean', 'new_data_var', 'new_data_sum', 'new_data_rep', 'new_data_SST'], inplace=True, axis=1)
        '''
        for c_subr_data_index in range(0, len(c_subr.pd_sample_record)):
            if c_subr.pd_sample_record.loc[c_subr_data_index, 'rep'] == 0:

                c_subr.pd_sample_record.loc[c_subr_data_index, 'mean'] = copy.copy(df_testing_samples_grouped_mean.loc[(df_testing_samples_grouped_mean[p['Name']] == c_subr.pd_sample_record[p['Name']] for p in params), 'result'])

                c_subr.pd_sample_record.loc[c_subr_data_index, 'SST'] = copy.copy(df_testing_samples_grouped_SST.loc[[df_testing_samples_grouped_SST[p['Name']] for p in params] == [c_subr.pd_sample_record[p['Name']] for p in params], 'result'])
                c_subr.pd_sample_record.loc[c_subr_data_index, 'var'] = copy.copy(df_testing_samples_grouped_var.loc[[df_testing_samples_grouped_var[p['Name']] for p in params] == [c_subr.pd_sample_record[p['Name']] for p in params], 'result'])
                c_subr.pd_sample_record.loc[c_subr_data_index, 'rep'] = i_n
            else:
                c_subr.pd_sample_record.loc[c_subr_data_index, 'mean'] = copy.copy(float(
                            int(c_subr.pd_sample_record.loc[c_subr_data_index, 'rep']) * c_subr.pd_sample_record.loc[c_subr_data_index, 'mean'] + df_testing_samples_grouped_var.loc[[df_testing_samples_grouped_sum[p['Name']] for p in params] == [c_subr.pd_sample_record[p['Name']] for p in params], 'result']) / i_n)
                c_subr.pd_sample_record.loc[c_subr_data_index, 'SST'] = copy.copy(c_subr.pd_sample_record.loc[c_subr_data_index, 'SST'] + df_testing_samples_grouped_SST.loc[[df_testing_samples_grouped_SST[p['Name']] for p in params] == [c_subr.pd_sample_record[p['Name']] for p in params], 'result'])
                c_subr.pd_sample_record.loc[c_subr_data_index, 'var'] = copy.copy(float(c_subr.pd_sample_record.loc[c_subr_data_index, 'SST'] - i_n * pow(c_subr.pd_sample_record.loc[c_subr_data_index, 'mean'], 2)) / (i_n - 1))
                c_subr.pd_sample_record.loc[c_subr_data_index, 'rep'] = i_n
         '''
    return l_subr

"""
This function orders all the sampling points in all the undetermined regions
input:
    one subregions
output:
    c_subregion:subregion with updated dataframe of descending order data
"""


def fun_order_subregion(c_subr):
    c_subr.pd_sample_record = c_subr.pd_sample_record.sort_values(by="mean", ascending=True)
    c_subr.pd_sample_record = c_subr.pd_sample_record.reset_index(drop=True)  # reindex the sorted df
    if len(c_subr.pd_sample_record) > 0:
        c_subr.i_min_sample = c_subr.pd_sample_record.loc[0, 'mean']
        c_subr.i_max_sample = c_subr.pd_sample_record.loc[len(c_subr.pd_sample_record)-1, 'mean']
    c_subr.f_min_diff_sample_mean = min(c_subr.pd_sample_record['mean'].shift(-1) - c_subr.pd_sample_record['mean'])
    c_subr.f_max_var = max(c_subr.pd_sample_record.loc[:, 'var'])
    return c_subr

"""
f_update_replication function is aim to calculate the updated replication number
input:
    l_subr:list of all examning subregions
    i_n_rep:original replication
    f_alpha
outout
    i_replication:update replication
"""


def fun_replication_update(l_subr, i_n_rep, f_alpha):
    if list(i.f_min_diff_sample_mean for i in l_subr if i.s_label == 'C' and i.b_activate is True) + [] == []: # to prevent empty sequence
        f_d_star = 0.005
    elif min(i.f_min_diff_sample_mean for i in l_subr if i.s_label == 'C' and i.b_activate is True) < 0.005:
        f_d_star = 0.005
    else:
        f_d_star = min(i.f_min_diff_sample_mean for i in l_subr if i.s_label == 'C' and i.b_activate is True)
    f_var_star = max(i.f_max_var for i in l_subr if i.s_label == 'C' and i.b_activate is True)
    z = scipy.stats.norm.ppf(1 - f_alpha / 2)
    # to prevent the float NaN
    if math.isnan(z) is True or math.isnan(f_d_star) is True or math.isnan(f_var_star) is True:
        i_n_rep = i_n_rep
    else:
        i_n_rep = max(i_n_rep, 4 * int(math.ceil(pow(z, 2) * f_var_star / pow(f_d_star, 2))))
    return i_n_rep

"""
This function orders all the sampling points in all the undetermined regions
input:
    l_subr:list of all subregions
output:
    pd_order_z:dataframe of descending order data
"""


def fun_order_region(l_subr):
    l_all_sample_C = []
    for i in (i for i in l_subr if i.s_label == 'C'):
        l_all_sample_C.append(i.pd_sample_record)
    pd_order_z = pd.concat(l_all_sample_C)
    pd_order_z = pd_order_z.sort_values(by="mean", ascending=True)
    pd_order_z = pd_order_z.reset_index(drop=True)  # reindex the sorted df
    return pd_order_z

"""
input: 
    f_CI_u:upper bound confidence interval
     c_subr: examining subregion
output:
    update subregions
"""


def fun_pruning_indicator(l_subr, f_CI_u):
    for c_subr in (c_subr for c_subr in l_subr if c_subr.s_label == 'C' and c_subr.b_activate is True and c_subr.b_worst is True):
        if c_subr.i_min_sample > f_CI_u:
            c_subr.b_maintaining_indicator = False
            c_subr.b_pruning_indicator = True
    return l_subr

"""
This function create the list of subregions prepared to maintain from the list of elite subregions 
nput: 
    f_CI_l:lower bound confidence interval
    c_subr: examining subregion
output:
   update subregions
"""


def fun_maintaining_indicator(l_subr, f_CI_l):
    for c_subr in (c_subr for c_subr in l_subr if c_subr.s_label == 'C' and c_subr.b_activate is True and c_subr.b_elite is True):
        if c_subr.i_max_sample < f_CI_l:
            c_subr.b_maintaining_indicator = True
            c_subr.b_pruning_indicator = False
    return l_subr

"""
This function create the list of worst function used in the step 4
nput: 
    f_CI_l:lower bound confidence interval
    c_subregions:examining subregion
output:
    list 0f update subregions
"""


def fun_elite_indicator(l_subr, f_CI_l):
    for c_subr in (c_subr for c_subr in l_subr if c_subr.s_label == 'C' and c_subr.b_activate is True and c_subr.i_max_sample < f_CI_l):
        c_subr.b_elite = True
        c_subr.b_worst = False
    return l_subr

"""
This function create the list of worst function used in the step 4
nput: 
    f_CI_u:upper bound confidence interval
    c_subregions:examining subregion
output:
    list 0f updated subregions
"""


def fun_worst_indicator(l_subr, f_CI_u):
    for c_subr in (c_subr for c_subr in l_subr if c_subr.s_label == 'C' and c_subr.b_activate is True and c_subr.i_min_sample > f_CI_u):
        c_subr.b_elite = False
        c_subr.b_worst = True
    return l_subr

"""
This function update the quantile
input:
    l_subr: list of subregions
    f_delta
output:
    f_delta:updated quantile
"""


def fun_quantile_update(l_subr, f_delta):
    f_vol_C = sum(c.f_volume for c in l_subr if c.s_label == 'C' and c.b_activate is True)
    f_vol_pruning = sum(c.f_volume for c in l_subr if c.b_pruning_indicator is True and c.b_activate is True)
    f_vol_maintaining = sum(c.f_volume for c in l_subr if c.b_maintaining_indicator is True and c.b_activate is True)
    f_delta = float(f_delta*f_vol_C-f_vol_maintaining)/(f_vol_C-f_vol_pruning-f_vol_maintaining)
    return f_delta


"""
input:
    l_subergion:examine subregions
    f_delta
    f_epsilon
    f_vol_S:volume of all regions
    f_vol_C:volume of set of all undetermined regions
    f_vol_P:volume of set of all prune regions
    f_vol_M:volume of set of all maintain regions

outout
    CI_l:lower bound of confident interval
    CI_u:upper bound of confident interval
"""


def fun_CI_builder(l_subr, pd_order_z, f_delta_k, f_alpha_k, f_epsilon):
    f_vol_S = l_subr[0].f_volume
    f_vol_C = sum(c.f_volume for c in l_subr if c.s_label == 'C' and c.b_activate is True)
    f_vol_P = sum(c.f_volume for c in l_subr if c.s_label == 'P' and c.b_activate is True)
    f_vol_M = sum(c.f_volume for c in l_subr if c.s_label == 'M' and c.b_activate is True)
    f_delta_kl = f_delta_k - float(f_vol_P * f_epsilon) / (f_vol_S * f_vol_C)
    f_delta_ku = f_delta_k + float(f_vol_M * f_epsilon) / (f_vol_S * f_vol_C)
    f_max_r = binom.ppf(f_alpha_k / 2, len(pd_order_z), f_delta_kl)
    f_min_s = binom.ppf(1 - f_alpha_k / 2, len(pd_order_z), f_delta_ku)
    if math.isnan(f_max_r) is True:
        f_max_r = 0
    CI_l = pd_order_z.loc[f_max_r, 'mean']
    CI_u = pd_order_z.loc[f_min_s, 'mean']
    return [CI_u, CI_l]



def fun_pruning_labeler(l_subr):
    for c_subr in (c_subr for c_subr in l_subr if c_subr.b_pruning_indicator is True and c_subr.b_activate is True):  # <-- whose  worst == 1
        c_subr.s_label = 'P'
    return l_subr


def fun_maintaining_labeler(l_subr):
    for c_subr in (c_subr for c_subr in l_subr if c_subr.b_maintaining_indicator is True and c_subr.b_activate is True):  # <-- whose elite == 1
        c_subr.s_label = 'M'
    return l_subr

"""
input:
    c_subr: examining subregion
output:
    l_subr: list of branching B subregions
"""


def fun_reg_branching(c_subr, i_n_branching, params, s_branching_dim):
    i_max_index = [p['Name'] for p in params].index(s_branching_dim)

    l_subr_new = []
    # the following creates B subregions in the list of subregions
    for i in range(0, i_n_branching):
        l_coordinate_lower = copy.deepcopy(c_subr.l_coordinate_lower)
        l_coordinate_upper = copy.deepcopy(c_subr.l_coordinate_upper)
        l_coordinate_lower[i_max_index] = float((c_subr.l_coordinate_upper[i_max_index] - c_subr.l_coordinate_lower[i_max_index])*i)/i_n_branching+c_subr.l_coordinate_lower[i_max_index]
        l_coordinate_upper[i_max_index] = float((c_subr.l_coordinate_upper[i_max_index] - c_subr.l_coordinate_lower[i_max_index])*(i+1))/i_n_branching+c_subr.l_coordinate_lower[i_max_index]
        l_new_branching_subr = c_SubRegion(l_coordinate_lower, l_coordinate_upper, params)
        l_subr_new.append(l_new_branching_subr)
    # the following reallocate the sampling points
    for i in l_subr_new:
        i.pd_sample_record = c_subr.pd_sample_record[(c_subr.pd_sample_record[s_branching_dim] > i.l_coordinate_lower[i_max_index]) & (c_subr.pd_sample_record[s_branching_dim] < i.l_coordinate_upper[i_max_index])]
    for i in l_subr_new:  # reindex the sampling points into 0 1 2...
        i.pd_sample_record = i.pd_sample_record.reset_index(drop=True)
        # update attributed based on data
        if len(i.pd_sample_record) > 0:
            i.i_min_sample = min(i.pd_sample_record.loc[:, 'mean'])
            i.i_max_sample = max(i.pd_sample_record.loc[:, 'mean'])
            i.f_min_diff_sample_mean = min(i.pd_sample_record['mean'].shift(-1) - i.pd_sample_record['mean'])
        if len(i.pd_sample_record) > 1:
            i.f_max_var = max(i.pd_sample_record.loc[:, 'var'])
    return l_subr_new


def fun_plot2D(l_subr, l_initial_coordinate_lower, l_initial_coordinate_upper, params, str_k, s_running_file_name, i_iteration):
    import matplotlib.patches as patches
    import matplotlib.pyplot as plt
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.plot(l_initial_coordinate_upper[0], l_initial_coordinate_upper[1])
    ax.plot(l_initial_coordinate_lower[0], l_initial_coordinate_lower[1])

    for c_subr in (c_subr for c_subr in l_subr if c_subr.b_activate is True):
        if c_subr.s_label == 'M':
            alpha_value = 1
        elif c_subr.s_label == 'P':
            alpha_value = 0.1
        else:  # i.s_label == 'C':
            alpha_value = 0.6
        ax.add_patch(
            patches.Rectangle(
                (c_subr.l_coordinate_lower[0], c_subr.l_coordinate_lower[1]),  # (x,y)
                c_subr.l_coordinate_upper[0] - c_subr.l_coordinate_lower[0],  # width
                c_subr.l_coordinate_upper[1] - c_subr.l_coordinate_lower[1],  # height
                alpha=alpha_value,
                edgecolor="black"
            )
        )
    # the following plot the minimum and maximum point
    df_all_sample = pd.concat([c_subr.pd_sample_record for c_subr in l_subr if c_subr.b_activate is True])
    df_all_sample = df_all_sample.sort_values(by="mean", ascending=True)  # sort before start
    df_all_sample = df_all_sample.reset_index(drop=True)
    f_min_value = df_all_sample.loc[0, 'mean']
    f_max_value = df_all_sample.loc[len(df_all_sample) - 1, 'mean']
    l_min_coordinate = [df_all_sample.loc[0, p['Name']] for p in params]
    l_max_coordinate = [df_all_sample.loc[len(df_all_sample) - 1, p['Name']] for p in params]
    p_min, p_max = ax.plot(l_min_coordinate[0], l_min_coordinate[1], '*b', l_max_coordinate[0], l_max_coordinate[1],
                           'or')
    fig.legend((p_min, p_max), (
        'minimum point:[' + str(l_min_coordinate[0]) + ',' + str(l_min_coordinate[1]) + '], result:' + str(f_min_value),
        'maximum point:[' + str(l_max_coordinate[0]) + ',' + str(l_max_coordinate[1]) + '], result:' + str(
            f_max_value)), 'upper right')

    for c_subr in (c_subr for c_subr in l_subr if c_subr.b_activate is True):
        ax.text(float(c_subr.l_coordinate_lower[0] + c_subr.l_coordinate_upper[0]) / 2,
                float(c_subr.l_coordinate_lower[1] + c_subr.l_coordinate_upper[1]) / 2,
                str(c_subr.pd_sample_record['rep'].sum()))
    # plt.legend(handles=[red_patch, blue_patch])
    i_total_simulation = 0
    for c_subr in (c_subr for c_subr in l_subr if c_subr.b_activate is True):
        i_total_simulation += (c_subr.pd_sample_record['rep'].sum())
    fig.text(0.02, 0.02, 'total number of simulation:' + str(i_total_simulation), fontsize=14)

    ax.set_xlabel([p['Name'] for p in params][0])
    ax.set_ylabel([p['Name'] for p in params][1])

    fig.savefig(s_running_file_name+'/iter'+str(i_iteration)+'/Region_Status ' + str(str_k) + '.pdf')
    #with open('l_subr_all_simulations_iteration' + str(str_k) + '.dat', "wb") as f:
    #    pickle.dump(l_subr, f)
    plt.close(fig)
