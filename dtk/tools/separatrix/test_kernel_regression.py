import math

import numpy as np
import matplotlib.pyplot as plt
import statsmodels.nonparametric.api as nparam

def KernelReg1D():
    np.random.seed(12345)
    nobs = 500

    x = np.random.uniform(-2, 2, size=nobs)
    x.sort()
    y_true = 0.05 + np.abs( 0.15 * (np.sin(x*5)/x + 2*x) )
    R = np.random.random(size=nobs)
    y = y_true>R

    model = nparam.KernelReg(endog=[y],
                             exog=[x],
                             reg_type='lc', # lc, ll
                             var_type='c',  # c, u, o
                             bw='cv_ls')    # cv_ls, aic

    sm_bw = model.bw

    sm_mean, sm_mfx = model.fit()

    fig = plt.figure('Test1D',figsize=(9,5))
    ax = fig.add_subplot(111)
    ax.plot(x, y, '+', alpha=0.5, ms=20, color='navy')
    ax.plot(x, y_true, lw=1, label='true mean')
    ax.plot(x, sm_mean, lw=1, label='kernel mean')
    ax.tick_params(direction='out')
    ax.set(xlim=[-2, 2],ylim=[0,1])
    ax.legend()

    plt.tight_layout()

def KernelReg2D():
    np.random.seed(12345)
    nobs = 500

    xy = np.random.uniform(0, 1, size=(nobs,2))
    tanh_fn = lambda x,y: math.tanh(x)*math.tanh(y)
    z_true = [tanh_fn(x,y) for (x,y) in xy]

    R = np.random.random(size=nobs)
    z = z_true>R

    model = nparam.KernelReg(endog=[z],
                             exog=[zip(*xy)],
                             reg_type='ll',  # 'lc' (local constant), 'll' (local linear)
                             var_type='cc',  # 'c' (continuous) -- for each variable in exog list
                             bw='cv_ls')     # cv_ls, aic

    X, Y = np.mgrid[0:1:100j, 0:1:100j]
    positions = np.vstack([X.ravel(), Y.ravel()]).T
    sm_mean, sm_mfx = model.fit(positions)
    Z = np.reshape(sm_mean, X.shape)
    Z_true = np.reshape([tanh_fn(x,y) for (x,y) in positions], X.shape)

    fig = plt.figure('Test2D',figsize=(12,5))

    color_args=dict(cmap='afmhot', vmin=0, vmax=1, alpha=0.5)

    ax = fig.add_subplot(121)
    im=ax.pcolor(X,Y,Z_true,**color_args)
    cax=ax.scatter(*zip(*xy), c=z_true, s=30, **color_args)
    ax.tick_params(direction='out')
    ax.set(xlim=[0,1],ylim=[0,1])
    fig.colorbar(cax)

    ax = fig.add_subplot(122)
    im=ax.pcolor(X,Y,Z,**color_args)
    cax=ax.scatter(*zip(*xy), c=z, s=20, **color_args)
    ax.tick_params(direction='out')
    ax.set(xlim=[0,1],ylim=[0,1])
    fig.colorbar(cax)

    plt.tight_layout()

if __name__ == '__main__':
    KernelReg1D()
    KernelReg2D()
    plt.show()