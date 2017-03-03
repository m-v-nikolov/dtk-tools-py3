import numpy as np
import scipy.stats as sps

def weib_cdf(x, lam, kap):
    return [1 - np.exp(-(xx / lam) ** kap) for xx in x]


def kstest(duration, fun, alpha):
    (D, p_val) = sps.kstest(duration, fun)

    if p_val < alpha:
        return {'Valid': False, 'Test_Statistic': D, 'P_Value': p_val}

    return {'Valid': True, 'Test_Statistic': D, 'P_Value': p_val}

