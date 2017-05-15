from __future__ import division
import numpy as np

import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from scipy.linalg import sqrtm
from numpy.linalg import matrix_rank
from numpy import inf


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


def likelihood(sigma, innovation):
    # Gaussian likelihood
    propFactor = 1 / np.sqrt(2 * np.pi * sigma)
    l = propFactor * np.exp(-0.5 * innovation ** 2 / sigma)
    # l = []
    # for i in range(len(innovation)):
    #    l.append(propFactor * np.exp(-0.5 * innovation[i]**2 /sigma))
    return l


def FisherInfMatrix(X, logL_fn, Perturb_size, M=10, N=1000):
    # dimension of X
    p = len(X)
    C = Perturb_size  # .05*(X_max -X_min)
    C_tilde = Perturb_size

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
        Delta = np.zeros(shape=(p, M))
        Delta_tilde = np.zeros(shape=(p, M))

        np.random.seed()
        if p == 2:
            DeltaMat = np.round(np.random.uniform(0, 1, (p, p))) * 2 - 1
            DeltatildeMat = np.round(np.random.uniform(0, 1, (p, p))) * 2 - 1
            while matrix_rank(DeltaMat) < p:
                DeltaMat = np.round(np.random.uniform(0, 1, (p, p))) * 2 - 1
            while matrix_rank(DeltatildeMat) < p:
                DeltatildeMat = np.round(np.random.uniform(0, 1, (p, p))) * 2 - 1
        else:
            DeltaMat = np.tile(np.round(np.random.uniform(0, 1, (p, 1))) * 2 - 1, (1, p))
            DeltatildeMat = np.tile(np.round(np.random.uniform(0, 1, (p, 1))) * 2 - 1, (1, p))

        for k in range(M):

            loc = k % p
            Delta[:, k] = DeltaMat[:, loc]
            Delta_tilde[:, k] = DeltatildeMat[:, loc]
            if p != 2:
                Delta[loc, k] = -1 * Delta[loc, k]
                Delta_tilde[loc, k] = -1 * Delta_tilde[loc, k]

            thetaPlus = X.T + (C * Delta[:, k])
            thetaMinus = X.T - (C * Delta[:, k])
            thetaPlusPlus = thetaPlus + C_tilde * Delta_tilde[:, k]
            thetaPlusMinus = thetaPlus - C_tilde * Delta_tilde[:, k]
            thetaMinusPlus = thetaMinus + C_tilde * Delta_tilde[:, k]
            thetaMinusMinus = thetaMinus - C_tilde * Delta_tilde[:, k]

            X_perturbs = np.concatenate((thetaPlusPlus.T, thetaPlusMinus.T, thetaMinusPlus.T, thetaMinusMinus.T),
                                        axis=1)
            [loglPP, loglPM, loglMP, loglMM] = logL_fn(X_perturbs, X)

            G_p[:, k] = (loglPP - loglPM) / (2 * C_tilde * Delta_tilde[:, k]).T
            G_m[:, k] = (loglMP - loglMM) / (2 * C_tilde * Delta_tilde[:, k]).T

            # H_hat(n)
            S = np.dot((1 / (2 * C * Delta[:, k]))[:, None], (G_p[:, k] - G_m[:, k])[None, :])  # H_hat
            H_hat[:, :, k] = .5 * (S + S.T)
            H_hat_avg[:, :, k] = k / (k + 1) * H_hat_avg[:, :, k - 1] + 1 / (k + 1) * H_hat[:, :, k]

        H_bar[:, :, i] = .5 * (H_hat_avg[:, :, M - 1] - sqrtm(np.linalg.matrix_power(H_hat_avg[:, :, M - 1], 2)))
        H_bar_avg[:, :, i] = i / (i + 1) * H_bar_avg[:, :, i - 1] + 1 / (i + 1) * H_bar[:, :, i]

    Fisher = -1 * H_bar_avg[:, :, N - 1]
    return Fisher


def logL_fn(X, X0):
    n = 50
    p = len(X0)
    sigma_obs = 0.01
    Z = []
    for j in range(n):
        Z.append(np.linalg.norm(X0 - np.ones(shape=(1, p))) + np.random.normal(0, sigma_obs))
    meanZ = np.mean(Z)
    stdZ = np.std(Z)
    logL_X = []
    for i in range(np.shape(X)[1]):
        zeta = np.linalg.norm(X[:, i] - np.ones(shape=(1, p))) + np.random.normal(0, sigma_obs)  # fValue(X)
        logL_X.append(np.log(likelihood(stdZ, abs(zeta - meanZ))))
    return logL_X


p = 2
X = np.random.uniform(0.0, 2.0, (p, 1))
X_min = 0
X_max = 2
M = 20
N = 1000
Perturb_size = .05 * (X_max - X_min)

# n = 10
# sigma_obs = 0.01
# Z = []
# for j in range(n):
#    Z.append(np.linalg.norm(X-np.ones(shape=(1,p))) + np.random.normal(0,sigma_obs))
Fisher = FisherInfMatrix(X, logL_fn, Perturb_size, M, N)

# sigma = diag(inv(Fisher))**.5
Covariance = np.linalg.inv(Fisher)

print "eigs of fisher: ", np.linalg.eigvals(Fisher)

print(Covariance)
fig3 = plt.figure('CramerRao')
ax = plt.subplot(111)
x, y = X[0:2]
plt.plot(x, y, 'g.')
plot_cov_ellipse(Covariance, X, nstd=1, alpha=0.6, color='green')
plt.xlim(0, 2)
plt.ylim(0, 2)
plt.xlabel('X', fontsize=14)
plt.ylabel('Y', fontsize=14)
plt.show()