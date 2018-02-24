import math

import numpy as np
from scipy.special import gammaln


"""
Functions below compare "ref" and "sim" columns of a pandas.DataFrame
"""


def dirichlet_multinomial_pandas(df):

    # Get the number of total observations aggregated over the last level in MultiIndex
    # e.g. if levels are ['Channel', 'Season', 'Age Bin', 'PfPR Bin']
    #      keep first three in index, while summing over the last level.
    sum_levels = df.index.names[:-1]
    n_obs = df.sum(level=sum_levels)
    n_categories = len(df.index.levels[-1])

    n_obs['LL'] = gammaln(n_obs.ref + 1) \
                + gammaln(n_obs.sim) \
                - gammaln(n_obs.ref + n_obs.sim + n_categories) \
                + gammaln(df.ref + df.sim + 1).sum(level=sum_levels) \
                - gammaln(df.sim + 1).sum(level=sum_levels) \
                - gammaln(df.ref + 1).sum(level=sum_levels)

    return n_obs.LL.mean() / n_categories


def gamma_poisson_pandas(df):

    LL = gammaln(df.ref.Observations + df.sim.Observations + 1) \
       - gammaln(df.ref.Observations + 1) \
       - gammaln(df.sim.Observations + 1)

    ix = df.ref.Trials > 0
    LL.loc[ix] += (df.loc[ix].ref.Observations + 1) * np.log(df.loc[ix].ref.Trials)

    ix = df.sim.Trials > 0
    LL.loc[ix] += (df.loc[ix].sim.Observations + 1) * np.log(df.loc[ix].sim.Trials)

    ix = (df.ref.Trials > 0) & (df.sim.Trials > 0)
    LL.loc[ix] -= (df.loc[ix].ref.Observations + df.loc[ix].sim.Observations + 1) \
                  * np.log(df.loc[ix].ref.Trials + df.loc[ix].sim.Trials)

    return LL.mean()


def beta_binomial_pandas(df):
    LL = gammaln(df.ref.Trials + 1) \
       + gammaln(df.sim.Trials + 2) \
       - gammaln(df.ref.Trials + df.sim.Trials + 2) \
       + gammaln(df.ref.Observations + df.sim.Observations + 1) \
       + gammaln(df.ref.Trials - df.ref.Observations + df.sim.Trials - df.sim.Observations + 1) \
       - gammaln(df.ref.Observations + 1) \
       - gammaln(df.ref.Trials - df.ref.Observations + 1) \
       - gammaln(df.sim.Observations + 1) \
       - gammaln(df.sim.Trials - df.sim.Observations + 1)

    return LL.mean()

"""
Functions below were ported by J.Gerardin
from K.McCarthy Matlab CalibTool versions
"""


def dirichlet_multinomial(raw_data, sim_data):

    num_age_bins = len(raw_data[:, 0])
    num_cat_bins = len(raw_data[0, :])
    raw_nobs = [sum(raw_data[i, :]) for i in range(num_age_bins)]
    sim_nobs = [sum(sim_data[i, :]) for i in range(num_age_bins)]
    
    LL = 0.
    for agebin in range(num_age_bins):
        LL += gammaln(raw_nobs[agebin] + 1) 
        LL += gammaln(sim_nobs[agebin]) 
        LL -= gammaln(raw_nobs[agebin] + sim_nobs[agebin] + num_cat_bins)
        for catbin in range(num_cat_bins):
            LL += gammaln(raw_data[agebin, catbin] + sim_data[agebin, catbin] + 1)
            LL -= gammaln(sim_data[agebin, catbin] + 1)
            LL -= gammaln(raw_data[agebin, catbin] + 1)

    LL /= (num_age_bins*num_cat_bins)
    return LL


def dirichlet_single(raw_data, sim_data):

    num_cat_bins = len(raw_data)
    raw_nobs = sum(raw_data)
    sim_nobs = sum(sim_data)
    
    LL = 0.
    LL += gammaln(raw_nobs + 1)
    LL += gammaln(sim_nobs + num_cat_bins)
    LL -= gammaln(raw_nobs + sim_nobs + num_cat_bins)
    for catbin in range(num_cat_bins) :
        LL += gammaln(raw_data[catbin] + sim_data[catbin] + 1)
        LL -= gammaln(sim_data[catbin] + 1)
        LL -= gammaln(raw_data[catbin] + 1)

    LL /= num_cat_bins
    return LL


def beta_binomial(raw_nobs, sim_nobs, raw_data, sim_data):
    
    num_bins = len(raw_data)
    
    LL = 0.
    for this_bin in range(num_bins):
        LL += gammaln(raw_nobs[this_bin] + 1)
        LL += gammaln(sim_nobs[this_bin] + 2)
        LL -= gammaln(raw_nobs[this_bin] + sim_nobs[this_bin] + 2)
        LL += gammaln(raw_data[this_bin] + sim_data[this_bin] + 1)
        LL += gammaln(raw_nobs[this_bin] - raw_data[this_bin] + sim_nobs[this_bin] - sim_data[this_bin] + 1)
        LL -= gammaln(raw_data[this_bin] + 1)
        LL -= gammaln(raw_nobs[this_bin] - raw_data[this_bin] + 1)
        LL -= gammaln(sim_data[this_bin] + 1)
        LL -= gammaln(sim_nobs[this_bin] - sim_data[this_bin] + 1)

    LL /= num_bins
    return LL


def gamma_poisson(raw_nobs, sim_nobs, raw_data, sim_data):
    
    num_bins = len(raw_data)
    
    LL = 0.
    for this_bin in range(num_bins):
        if raw_nobs[this_bin] > 0:
            LL += (raw_data[this_bin] + 1) * math.log(raw_nobs[this_bin])
        if sim_nobs[this_bin] > 0:
            LL += (sim_data[this_bin] + 1) * math.log(sim_nobs[this_bin])
        if raw_nobs[this_bin] + sim_nobs[this_bin] > 0:
            LL -= (raw_data[this_bin] + sim_data[this_bin] + 1) * math.log(raw_nobs[this_bin] + sim_nobs[this_bin])
        LL += gammaln(raw_data[this_bin] + sim_data[this_bin] + 1)
        LL -= gammaln(raw_data[this_bin] + 1)
        LL -= gammaln(sim_data[this_bin] + 1)

    if num_bins != 0:
        LL /= num_bins
    return LL

"""
Other weighting functions
"""


def euclidean_distance(raw_data, sim_data):

    num_obs = len(raw_data)
    return math.sqrt(sum([(raw_data[x] - sim_data[x])**2 for x in range(num_obs)]))*-1


def euclidean_distance_pandas(df):

    return math.sqrt(np.sum((np.array(df.ref) - np.array(df.sim)) ** 2)) * -1


def weighted_squares(raw_data, sim_data):

    num_obs = len(raw_data)
    return math.sqrt(sum([(raw_data[x] - sim_data[x])**2/raw_data[x] for x in range(num_obs)]))*-1