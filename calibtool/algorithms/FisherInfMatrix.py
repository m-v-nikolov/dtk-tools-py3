from __future__ import division
import numpy as np

import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from scipy.linalg import sqrtm


# from numpy.linalg import matrix_rank
# from numpy import inf



def perturbed_points(X, pert_size, M):
    # % Atiye Alaeddini, 06/06/2017
    # % generate perturbed X and their corresponding log likelihood function
    #
    # % ------------------------------------------------------------------------
    # % INPUTS:
    # % X           ----- center point ---------------------------------- px1
    # % pert_size   ----- size of the perturbation ---------------------- px1
    # % M           ----- number of Hessian estimates
    #
    # % ------------------------------------------------------------------------
    # % OUTPUTS:
    # % X_perturbed ----- perturbed points ----------------------------   px4xM
    # % Y_perturbed ----- cost values of perturbed points -------------   4xM


    # dimension of X
    p = len(X)
    C = np.random.uniform(low=0.5, high=2.0) * Perturb_size  # .05*(X_max -X_min)
    C_tilde = np.random.uniform(low=0.5, high=1.0) * C

    X_perturbed = np.zeros(shape=(p, 4, M))  # np.tile(X, (M+1,1))
    Y_perturbed = np.zeros(shape=(4, M))
    # X_perturbed[:,0] = X
    # Y_perturbed[0] = LogL_func(X_perturbed[:,0])
    if p != 2:
        Delta = np.ones(shape=(p, 1))
        Delta_tilde = np.ones(shape=(p, 1))

    for k in range(M):
        np.random.seed()
        # loc = np.random.permutation(p)[0]
        if p == 2:
            Delta = np.random.choice([-1, 1], size=(p, 1))
            Delta_tilde = np.random.choice([-1, 1], size=(p, 1))
        else:
            Delta[np.random.permutation(p)[0]] = -1 * Delta[np.random.permutation(p)[0]]
            Delta_tilde[np.random.permutation(p)[0]] = -1 * Delta_tilde[np.random.permutation(p)[0]]

        thetaPlus = X + (C * Delta)
        thetaMinus = X - (C * Delta)

        X_perturbed[:, [0], k] = thetaPlus + C_tilde * Delta_tilde  # thetaPlusPlus
        Y_perturbed[0, k] = LogL_func(X_perturbed[:, 0, k])  # loglPP

        X_perturbed[:, [1], k] = thetaPlus - C_tilde * Delta_tilde  # thetaPlusMinus
        Y_perturbed[1, k] = LogL_func(X_perturbed[:, 1, k])  # loglPM

        X_perturbed[:, [2], k] = thetaMinus + C_tilde * Delta_tilde  # thetaMinusPlus
        Y_perturbed[2, k] = LogL_func(X_perturbed[:, 2, k])  # loglMP

        X_perturbed[:, [3], k] = thetaMinus - C_tilde * Delta_tilde  # thetaMinusMinus
        Y_perturbed[3, k] = LogL_func(X_perturbed[:, 3, k])  # loglMM

    return (X_perturbed, Y_perturbed)


def FisherInfMatrix(X, Perturb_size, M=10000, N=1):
    # dimension of X
    p = len(X)
    # Hessian
    H_bar = np.zeros(shape=(p, p, N))
    H_bar_avg = np.zeros(shape=(p, p, N))

    for i in range(N):
        # reset the data (samples) used for evaluation of the log likelihood
        # initialization
        H_hat = np.zeros(shape=(p, p, M))
        H_hat_avg = np.zeros(shape=(p, p, M))
        G_p = np.zeros(shape=(p, M))
        G_m = np.zeros(shape=(p, M))

        (X_perturbed, Y_perturbed) = perturbed_points(X, Perturb_size, M)

        for k in range(M):
            # print('X_perturbed = ', X_perturbed[:,:,k])
            # print('Y_perturbed = ', Y_perturbed[:,k])

            [thetaPlusPlus, thetaPlusMinus, thetaMinusPlus, thetaMinusMinus] = X_perturbed[:, :, k].T
            [loglPP, loglPM, loglMP, loglMM] = Y_perturbed[:, k]

            #print('Y_perturbed[:, k] = ', Y_perturbed[:, k])
            #print('thetaPlusPlus=',thetaPlusPlus)
            #print('thetaPlusMinus=',thetaPlusMinus)
            #print('loglPP=',loglPP)
            #print('loglPM=',loglPM)
            #print('loglMP=',loglMP)
            #print('loglMM=',loglMM)

            G_p[:, k] = (loglPP - loglPM) / (thetaPlusPlus - thetaPlusMinus)
            G_m[:, k] = (loglMP - loglMM) / (thetaMinusPlus - thetaMinusMinus)

            # H_hat(n)
            S = np.dot((1 / (thetaPlusPlus - thetaMinusPlus))[:, None], (G_p[:, k] - G_m[:, k])[None, :])  # H_hat
            # print('S=',S)

            H_hat[:, :, k] = .5 * (S + S.T)
            #print('H_hat_%d:\n'%k, H_hat[:, :, k])

            H_hat_avg[:, :, k] = k / (k + 1) * H_hat_avg[:, :, k - 1] + 1 / (k + 1) * H_hat[:, :, k]

        # print('G_p=',G_p)
        # print('G_m=',G_m)

        # TEMP
        #print 'A:\n', H_hat_avg[:, :, M - 1]
        #print 'B:\n', sqrtm(np.linalg.matrix_power(H_hat_avg[:, :, M - 1], 2) + 1e-6 * np.eye(p))
        #print 'C:\n', H_hat_avg[:, :, M - 1] - sqrtm(np.linalg.matrix_power(H_hat_avg[:, :, M - 1], 2) + 1e-6 * np.eye(p))

        H_bar[:, :, i] = .5 * (
            H_hat_avg[:, :, M - 1] - sqrtm(np.linalg.matrix_power(H_hat_avg[:, :, M - 1], 2) + 1e-6 * np.eye(p))
        )
        # print 'H_bar[:,:,i]=',H_bar[:,:,i]
        H_bar_avg[:, :, i] = i / (i + 1) * H_bar_avg[:, :, i - 1] + 1 / (i + 1) * H_bar[:, :, i]

    Fisher = -1 * H_bar_avg[:, :, N - 1]
    return Fisher


# plot the covarience matrix
def plot_cov_ellipse(cov, pos, nstd=2, ax=None, **kwargs):
    """
    Plots an `nstd` sigma error ellipse based on the specified covariance
    matrix (`cov`). Additional keyword arguments are passed on to the
    ellipse patch artist.

    Parameters
    ----------
        cov : The 2x2 covariance matrix to base the ellipse on
        pos : The location of the center of the ellipse. Expects a 2-element
            sequence of [x0, y0].
        nstd : The radius of the ellipse in numbers of standard deviations.
            Defaults to 2 standard deviations.
        ax : The axis that the ellipse will be plotted on. Defaults to the
            current axis.
        Additional keyword arguments are pass on to the ellipse patch.

    Returns
    -------
        A matplotlib ellipse artist
    """

    def eigsorted(cov):
        vals, vecs = np.linalg.eigh(cov)
        order = vals.argsort()[::-1]
        return vals[order], vecs[:, order]

    if ax is None:
        ax = plt.gca()

    vals, vecs = eigsorted(cov)
    theta = np.degrees(np.arctan2(*vecs[:, 0][::-1]))

    # Width and height are "full" widths, not radius
    width, height = 2 * nstd * np.sqrt(vals)
    ellip = Ellipse(xy=pos, width=width, height=height, angle=theta, **kwargs)

    ax.add_artist(ellip)
    return ellip


# test the algorithm
def log_likelihood(sigma, innovation):

    # TEMPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
    sigma = 0.1

    # Gaussian likelihood
    #print sigma, sigma**2
    propFactor = 1 / np.sqrt(2 * np.pi * sigma**2)
    #print 'propFactor', propFactor
    #print 'innovation', innovation
    ll = np.log(propFactor) + -0.5 * innovation ** 2 / sigma**2
    #print 'll', ll
    return ll


def LogL_func(X, sigma_obs = .1):
    n = 50
    p = len(X0)
    Z = []
    for j in range(n):
        Z.append(np.linalg.norm(X0 - np.ones(shape=(1, p))) + np.random.normal(0, sigma_obs))
    meanZ = np.mean(Z)
    stdZ = np.std(Z)
    logL_X = []
    zeta = np.linalg.norm(X - np.ones(shape=(1, p))) + np.random.normal(0, sigma_obs)  # fValue(X)
    #print 'stdZ', stdZ
    #print 'zeta - meanZ', zeta - meanZ
    logL_X = log_likelihood(stdZ, zeta - meanZ)
    # logL_X = np.log(likelihood(sigma_obs, np.linalg.norm(X)))
    # for i in range(np.shape(X)[1]):
    #    zeta = np.linalg.norm(X[:,i]-np.ones(shape=(1,p))) + np.random.normal(0,sigma_obs) #fValue(X)
    #    logL_X.append(np.log(likelihood(stdZ, abs(zeta-meanZ))))
    return logL_X

p = 2
global X0
X0 = np.random.uniform(0.0, 2.0, (p, 1))
print('X0 =', X0)
X_min = 0
X_max = 2
M = 10
N = 100
Perturb_size = .1 * (X_max - X_min)
Fisher = FisherInfMatrix(X0, Perturb_size, M, N)

# sigma = diag(inv(Fisher))**.5
Covariance = np.linalg.inv(Fisher)

print("eigs of fisher: ", np.linalg.eigvals(Fisher))
print("eigs of Covariance: ", np.linalg.eigvals(Covariance))

#print(Covariance)
fig3 = plt.figure('CramerRao')
ax = plt.subplot(111)
x, y = X0[0:2]
plt.plot(x, y, 'g.')
plot_cov_ellipse(Covariance, X0, nstd=1, alpha=0.6, color='green')
plt.xlim(-1, 3)
plt.ylim(-1, 3)
plt.xlabel('X', fontsize=14)
plt.ylabel('Y', fontsize=14)

# Plot the LL function in the background
x = y = np.arange(-1, 3, 0.1)
D = len(x)
X, Y = np.meshgrid(x, y)

Xs = X.reshape( np.prod(X.shape), 1)
Ys = Y.reshape( np.prod(Y.shape), 1)

Xvec = np.concatenate((Xs, Ys), axis=1)

def dummpy_fun(X, sigma_obs):
    #print 'X in df:\n', X
    return (X[0]-1)**2 + (X[1]-1)**2

from functools import partial
#Zs = np.apply_along_axis( partial(LogL_func, sigma_obs=0), axis=1, arr=Xvec)
Zs = np.apply_along_axis( partial(dummpy_fun, sigma_obs=0), axis=1, arr=Xvec)
Zmin = np.min(Zs)
Zmax = np.max(Zs)
CS = plt.contourf(X, Y, Zs.reshape(D,D), levels=np.linspace(Zmin, Zmax, 25), cmap='bone')

plt.show()
