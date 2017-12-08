import numpy as np
import scipy.stats as sps
import math


def weib_cdf(x, lam, kap):
    return [1 - np.exp(-(xx / lam) ** kap) for xx in x]


def binom_test(success, fail, prob_success, alpha):
    # print(fail, prob_success, alpha)
    p_val = sps.binom_test( success, fail, p=prob_success)
    return {'Valid': p_val >= alpha, 'Test_Statistic': success/fail, 'P_Value': p_val}


def kstest(duration, fun, alpha):
    # print(duration, fun, alpha)
    (D, p_val) = sps.kstest(duration, fun)

    if p_val < alpha:
        return {'Valid': False, 'Test_Statistic': D, 'P_Value': p_val}

    return {'Valid': True, 'Test_Statistic': D, 'P_Value': p_val}


def ztest(x, n, p, alpha):
    # print(x, n, p, alpha)
    if n*p < 10 or n*(1-p) < 10:
        print("WARNING: not enough samples to use a Z-Test, marking as Fail!")
        return {'Valid': False, 'Test_Statistic': None, 'P_Value': None}

    p_hat = x / float(n)
    std = math.sqrt( p*(1-p)/float(n) )
    z_score = (p_hat - p) / std
    p_val = 2 * sps.norm.cdf(-abs(z_score))

    if p_val < alpha:
        return {'Valid': False, 'Test_Statistic': z_score, 'P_Value': p_val}

    return {'Valid': True, 'Test_Statistic': z_score, 'P_Value': p_val}

