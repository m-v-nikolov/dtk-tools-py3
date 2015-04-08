from scipy.special import gamma, gammaln
import math

# all functions based on K McCarthy's Matlab CalibTool versions

def dirichlet_multinomial(raw_data, sim_data) :

    num_age_bins = len(raw_data[:, 0])
    num_cat_bins = len(raw_data[0, :])
    raw_nobs = [sum(raw_data[i, :]) for i in range(num_age_bins)]
    sim_nobs = [sum(sim_data[i, :]) for i in range(num_age_bins)]
    
    LL = 0.
    for agebin in range(num_age_bins) :
        LL += gammaln(raw_nobs[agebin] + 1) 
        LL += gammaln(sim_nobs[agebin]) 
        LL -= gammaln(raw_nobs[agebin] + sim_nobs[agebin] + num_cat_bins)
        for catbin in range(num_cat_bins) :
            LL += gammaln(raw_data[agebin, catbin] + sim_data[agebin, catbin] + 1)
            LL -= gammaln(sim_data[agebin, catbin] + 1)
            LL -= gammaln(raw_data[agebin, catbin] + 1)

    LL /= (num_age_bins*num_cat_bins)
    return LL

def dirichlet_single(raw_data, sim_data) :

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

def beta_binomial(raw_nobs, sim_nobs, raw_data, sim_data) :
    
    num_bins = len(raw_data)
    
    LL = 0.
    for this_bin in range(num_bins) :
        LL += gammaln(raw_nobs[this_bin] + 1)
        LL += gammaln(sim_nobs[this_bin] + 2)
        LL -= gammaln(raw_nobs[this_bin] + sim_nobs[this_bin] + 2)
        LL += gammaln(raw_data[this_bin] + sim_data[this_bin] + 1)
        LL += gammaln(raw_nobs[this_bin] - raw_data[this_bin] + sim_nobs[this_bin] - sim_data[this_bin] + 1)
        LL -= gammaln(raw_data[this_bin] + 1)
        LL -= gammaln(raw_nobs[this_bin] - raw_data[this_bin] + 1)
        LL -= gammaln(sim_data[this_bin] + 1)
        LL -= gammaln(sim_nobs[this_bin] - sim_data[this_bin] + 1)

    LL /= (num_bins)
    return LL


def gamma_poisson(raw_nobs, sim_nobs, raw_data, sim_data) :
    
    num_bins = len(raw_data)
    
    LL = 0.
    for this_bin in range(num_bins) :
        if raw_nobs[this_bin] > 0 :
            LL += (raw_data[this_bin] + 1) * math.log(raw_nobs[this_bin])
        if sim_nobs[this_bin] > 0 :
            LL += (sim_data[this_bin] + 1) * math.log(sim_nobs[this_bin])
        if raw_nobs[this_bin] + sim_nobs[this_bin] > 0 :
            LL -= (raw_data[this_bin] + sim_data[this_bin] + 1) * math.log(raw_nobs[this_bin] + sim_nobs[this_bin])
        LL += gammaln(raw_data[this_bin] + sim_data[this_bin] + 1)
        LL -= gammaln(raw_data[this_bin] + 1)
        LL -= gammaln(sim_data[this_bin] + 1)

    LL /= num_bins
    return LL
