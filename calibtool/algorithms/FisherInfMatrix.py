from __future__ import division
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from scipy.linalg import sqrtm


def perturbed_points(center, Xmin, Xmax, M=1, N=10, n=2, resolution=None):
    """
    Atiye Alaeddini, 12/11/2017
    generate perturbed points around the center

     ------------------------------------------------------------------------
    INPUTS:
    center    center point    1xp nparray
    Xmin    minimum of parameters    1xp nparray
    Xmax    maximum of parameters    1xp nparray
    M    number of Hessian estimates    scalar-positive integer
    N    number of pseudodata vectors    scalar-positive integer
    n    sample size    scalar-positive integer
    resolution    minimum perturbation for each parameter    1xp nparray
     ------------------------------------------------------------------------
    OUTPUTS:
    X_perturbed    perturbed points    (4MNn x 4+p) nparray
     ------------------------------------------------------------------------
    """
    # dimension of center point
    p = len(center)

    if resolution is None:
        resolution = 0.01*np.ones(p)

    X_scaled = (center - Xmin) / (Xmax - Xmin)

    # perturbation sizes
    C = 0.05*np.ones(p)#*(Xmax -Xmin)

    # making sure all plus/minus points in range
    too_big = (X_scaled + C) > 1
    too_small = (X_scaled - C) < 0
    C[too_big] = np.maximum(1 - X_scaled[too_big], resolution[too_big])
    C[too_small] = np.maximum(X_scaled[too_small], resolution[too_small])

    X_perturbed = np.zeros(shape=(4*M*N*n, 4+p))
    X_perturbed[:, 0] = np.tile(range(4), N * n * M).astype(int)
    X_perturbed[:, 1] = np.repeat(range(N),4 * n * M)
    X_perturbed[:, 2] = np.tile(np.repeat(range(M), 4 * n), N)

    counter = 0
    for j in range(N):
        run_numbers = np.random.randint(1,101,n)
        X_perturbed[(j*(4*n*M)):((j+1)*(4*n*M)), 3] = np.tile(np.repeat(run_numbers, 4), M)

        for k in range(M):

            np.random.seed()

            # perturbation vectors
            Delta = np.random.choice([-1, 1], size=(1,p))
            thetaPlus = X_scaled + (C * Delta)
            thetaMinus = X_scaled - (C * Delta)

            if (0 > thetaPlus).any() or (thetaPlus > 1).any():
                thetaPlus = X_scaled

            if (thetaMinus < 0).any() or (thetaMinus > 1).any():
                thetaMinus = X_scaled

            Delta_tilde = np.random.choice([-1, 1], size=(1,p))
            C_tilde = np.random.uniform(low=0.25, high=0.75) * C

            thetaPlusPlus = thetaPlus + C_tilde * Delta_tilde
            thetaPlusMinus = thetaPlus - C_tilde * Delta_tilde
            thetaMinusPlus = thetaMinus + C_tilde * Delta_tilde
            thetaMinusMinus = thetaMinus - C_tilde * Delta_tilde

            while (((0 > thetaPlusPlus).any() or (thetaPlusPlus > 1).any()) and
                       ((thetaPlusMinus < 0).any() or (thetaPlusMinus > 1).any())) or \
                    (((0 > thetaMinusPlus).any() or (thetaMinusPlus > 1).any()) and
                         ((thetaMinusMinus < 0).any() or (thetaMinusMinus > 1).any())):
                Delta_tilde = np.random.choice([-1, 1], size=(1,p))
                C_tilde = np.random.uniform(low=0.25, high=0.5) * C
                thetaPlusPlus = thetaPlus + C_tilde * Delta_tilde
                thetaPlusMinus = thetaPlus - C_tilde * Delta_tilde
                thetaMinusPlus = thetaMinus + C_tilde * Delta_tilde
                thetaMinusMinus = thetaMinus - C_tilde * Delta_tilde

            if ((0 > thetaPlusPlus).any() or (thetaPlusPlus > 1).any()):
                thetaPlusPlus = thetaPlus

            if ((0 > thetaMinusPlus).any() or (thetaMinusPlus > 1).any()):
                thetaMinusPlus = thetaMinus

            if ((0 > thetaPlusMinus).any() or (thetaPlusMinus > 1).any()):
                thetaPlusMinus = thetaPlus

            if ((0 > thetaMinusMinus).any() or (thetaMinusMinus > 1).any()):
                thetaMinusMinus = thetaMinus

            # back to original scale
            thetaPlusPlus_realValue = thetaPlusPlus * (Xmax - Xmin) + Xmin
            thetaPlusMinus_realValue = thetaPlusMinus * (Xmax - Xmin) + Xmin
            thetaMinusPlus_realValue = thetaMinusPlus * (Xmax - Xmin) + Xmin
            thetaMinusMinus_realValue = thetaMinusMinus * (Xmax - Xmin) + Xmin
            X_perturbed[(counter + 0):(counter + 4*n+0):4, 4:] = np.tile(thetaPlusPlus_realValue, (n,1))
            X_perturbed[(counter + 1):(counter + 4*n+1):4, 4:] = np.tile(thetaPlusMinus_realValue, (n,1))
            X_perturbed[(counter + 2):(counter + 4*n+2):4, 4:] = np.tile(thetaMinusPlus_realValue, (n,1))
            X_perturbed[(counter + 3):(counter + 4*n+3):4, 4:] = np.tile(thetaMinusMinus_realValue, (n,1))

            counter += 4*n

    # X_perturbed[:,0:4] = X_perturbed[:,0:4].astype(int)
    # convert to pandas DataFrame
    df_perturbed = pd.DataFrame(data=X_perturbed, columns=(['i','j','k','l']+['theta']*p))

    return df_perturbed



def FisherInfMatrix(center, df_perturbed_points, df_LL_points):
    """
    Atiye Alaeddini, 12/15/2017
    compute the Fisher Information matrix using the LL of perturbed points

     ------------------------------------------------------------------------
    INPUTS:
    center    center point    (1 x p) nparray
    df_perturbed_points    perturbed points    DataFrame
    df_LL_points    Log Likelihood of points    DataFrame
     ------------------------------------------------------------------------
    OUTPUTS:
    Fisher    Fisher Information matrix    (p x p) np array
     ------------------------------------------------------------------------
    """

    # convert DataFrame to python array
    LL_data = df_LL_points.as_matrix()
    points = df_perturbed_points.as_matrix()

    N = (max(points[:,1]) + 1).astype(int)
    M = (max(points[:, 2]) + 1).astype(int)
    n = int((np.shape(points)[0])/(4*M*N))

    PlusPlusPoints = points[0:(4 * M * N * n):(4 * n), 4:]
    PlusMinusPoints = points[1:(4 * M * N * n):(4 * n), 4:]
    MinusPlusPoints = points[2:(4 * M * N * n):(4 * n), 4:]
    MinusMinusPoints = points[3:(4 * M * N * n):(4 * n), 4:]

    # dimension of X
    p = len(center)

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

        PlusPlus_round_i = PlusPlusPoints[(i * M):((i + 1) * M), :]
        PlusMinus_round_i = PlusMinusPoints[(i * M):((i + 1) * M), :]
        MinusPlus_round_i = MinusPlusPoints[(i * M):((i + 1) * M), :]
        MinusMinus_round_i = MinusMinusPoints[(i * M):((i + 1) * M), :]

        loglPP_round_i = LL_data[(i * 4 * M + 0):((i + 1) * 4 * M + 0), 3]
        loglPM_round_i = LL_data[(i * 4 * M + 1):((i + 1) * 4 * M + 1), 3]
        loglMP_round_i = LL_data[(i * 4 * M + 2):((i + 1) * 4 * M + 2), 3]
        loglMM_round_i = LL_data[(i * 4 * M + 3):((i + 1) * 4 * M + 3), 3]

        for k in range(M):

            thetaPlusPlus = PlusPlus_round_i[k]
            thetaPlusMinus = PlusMinus_round_i[k]
            thetaMinusPlus = MinusPlus_round_i[k]
            thetaMinusMinus = MinusMinus_round_i[k]

            loglPP = loglPP_round_i[k]
            loglPM = loglPM_round_i[k]
            loglMP = loglMP_round_i[k]
            loglMM = loglMM_round_i[k]

            G_p[:, k] = (loglPP - loglPM) / (thetaPlusPlus - thetaPlusMinus)
            G_m[:, k] = (loglMP - loglMM) / (thetaMinusPlus - thetaMinusMinus)

            # H_hat(n)
            S = np.dot((1 / (thetaPlusPlus - thetaMinusPlus))[:, None], (G_p[:, k] - G_m[:, k])[None, :])  # H_hat
            H_hat[:, :, k] = .5 * (S + S.T)

            H_hat_avg[:, :, k] = k / (k + 1) * H_hat_avg[:, :, k - 1] + 1 / (k + 1) * H_hat[:, :, k]

        H_bar[:, :, i] = .5 * (
            H_hat_avg[:, :, M - 1] - sqrtm(np.linalg.matrix_power(H_hat_avg[:, :, M - 1], 2) + 1e-6 * np.eye(p))
        )
        H_bar_avg[:, :, i] = i / (i + 1) * H_bar_avg[:, :, i - 1] + 1 / (i + 1) * H_bar[:, :, i]

    Fisher = -1 * H_bar_avg[:, :, N - 1]
    return Fisher

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


# test
center = np.array([0.05,-0.92,-.98])
Xmin = np.array([-1]*3)
Xmax = np.array([1]*3)
df_perturbed_points = perturbed_points(center, Xmin, Xmax, M=2, N=5)
#print df_perturbed_points
# df_perturbed_points.to_csv("data.csv")
ll = pd.DataFrame.from_csv("LLdata.csv")
Fisher = FisherInfMatrix(center, df_perturbed_points, ll)
Covariance = np.linalg.inv(Fisher)

print("eigs of fisher: ", np.linalg.eigvals(Fisher))
print("eigs of Covariance: ", np.linalg.eigvals(Covariance))

fig3 = plt.figure('CramerRao')
ax = plt.subplot(111)
x, y = center[0:2]
plt.plot(x, y, 'g.')
plot_cov_ellipse(Covariance[0:2,0:2], center[0:2], nstd=1, alpha=0.6, color='green')
plt.xlim(Xmin[0], Xmax[0])
plt.ylim(Xmin[1], Xmax[1])
plt.xlabel('X', fontsize=14)
plt.ylabel('Y', fontsize=14)

plt.show()











# def perturbed_points(X, perturb_size, M):
#     # % Atiye Alaeddini, 12/11/2017
#     # % generate perturbed X and their corresponding log likelihood function
#     #
#     # % ------------------------------------------------------------------------
#     # % INPUTS:
#     # % X           ----- center point ---------------------------------- px1
#     # % pert_size   ----- size of the perturbation ---------------------- px1
#     # % M           ----- number of Hessian estimates
#     #
#     # % ------------------------------------------------------------------------
#     # % OUTPUTS:
#     # % X_perturbed ----- perturbed points ----------------------------   px4xM
#     # % Y_perturbed ----- cost values of perturbed points -------------   4xM
#
#
#     # dimension of X
#     p = len(X)
#     C = np.random.uniform(low=0.5, high=2.0) * perturb_size  # .05*(X_max -X_min)
#     C_tilde = np.random.uniform(low=0.5, high=1.0) * C
#
#     X_perturbed = np.zeros(shape=(p, 4, M))  # np.tile(X, (M+1,1))
#     Y_perturbed = np.zeros(shape=(4, M))
#     # X_perturbed[:,0] = X
#     # Y_perturbed[0] = LogL_func(X_perturbed[:,0])
#     if p != 2:
#         Delta = np.ones(shape=(p, 1))
#         Delta_tilde = np.ones(shape=(p, 1))
#
#     for k in range(M):
#         np.random.seed()
#         # loc = np.random.permutation(p)[0]
#         if p == 2:
#             Delta = np.random.choice([-1, 1], size=(p, 1))
#             Delta_tilde = np.random.choice([-1, 1], size=(p, 1))
#         else:
#             Delta[np.random.permutation(p)[0]] = -1 * Delta[np.random.permutation(p)[0]]
#             Delta_tilde[np.random.permutation(p)[0]] = -1 * Delta_tilde[np.random.permutation(p)[0]]
#
#         thetaPlus = X + (C * Delta)
#         thetaMinus = X - (C * Delta)
#
#         X_perturbed[:, [0], k] = thetaPlus + C_tilde * Delta_tilde  # thetaPlusPlus
#         Y_perturbed[0, k] = LogL_func(X_perturbed[:, 0, k])  # loglPP
#
#         X_perturbed[:, [1], k] = thetaPlus - C_tilde * Delta_tilde  # thetaPlusMinus
#         Y_perturbed[1, k] = LogL_func(X_perturbed[:, 1, k])  # loglPM
#
#         X_perturbed[:, [2], k] = thetaMinus + C_tilde * Delta_tilde  # thetaMinusPlus
#         Y_perturbed[2, k] = LogL_func(X_perturbed[:, 2, k])  # loglMP
#
#         X_perturbed[:, [3], k] = thetaMinus - C_tilde * Delta_tilde  # thetaMinusMinus
#         Y_perturbed[3, k] = LogL_func(X_perturbed[:, 3, k])  # loglMM
#
#     return (X_perturbed, Y_perturbed)
#
#
# def FisherInfMatrix(X, Perturb_size, M=10000, N=1):
#     # dimension of X
#     p = len(X)
#     # Hessian
#     H_bar = np.zeros(shape=(p, p, N))
#     H_bar_avg = np.zeros(shape=(p, p, N))
#
#     for i in range(N):
#         # reset the data (samples) used for evaluation of the log likelihood
#         # initialization
#         H_hat = np.zeros(shape=(p, p, M))
#         H_hat_avg = np.zeros(shape=(p, p, M))
#         G_p = np.zeros(shape=(p, M))
#         G_m = np.zeros(shape=(p, M))
#
#         (X_perturbed, Y_perturbed) = perturbed_points(X, Perturb_size, M)
#
#         for k in range(M):
#             # print 'X_perturbed = ', X_perturbed[:,:,k]
#             # print 'Y_perturbed = ', Y_perturbed[:,k]
#
#             [thetaPlusPlus, thetaPlusMinus, thetaMinusPlus, thetaMinusMinus] = X_perturbed[:, :, k].T
#             [loglPP, loglPM, loglMP, loglMM] = Y_perturbed[:, k]
#             #print 'Y_perturbed[:, k] = ', Y_perturbed[:, k]
#             #print 'thetaPlusPlus=',thetaPlusPlus
#             #print 'thetaPlusMinus=',thetaPlusMinus
#             #print 'loglPP=',loglPP
#             #print 'loglPM=',loglPM
#             #print 'loglMP=',loglMP
#             #print 'loglMM=',loglMM
#
#             G_p[:, k] = (loglPP - loglPM) / (thetaPlusPlus - thetaPlusMinus)
#             G_m[:, k] = (loglMP - loglMM) / (thetaMinusPlus - thetaMinusMinus)
#
#             # H_hat(n)
#             S = np.dot((1 / (thetaPlusPlus - thetaMinusPlus))[:, None], (G_p[:, k] - G_m[:, k])[None, :])  # H_hat
#             #print 'S=',S
#             H_hat[:, :, k] = .5 * (S + S.T)
#             #print 'H_hat_%d:\n'%k, H_hat[:, :, k]
#
#             H_hat_avg[:, :, k] = k / (k + 1) * H_hat_avg[:, :, k - 1] + 1 / (k + 1) * H_hat[:, :, k]
#
#         # print 'G_p=',G_p
#         # print 'G_m=',G_m
#
#         # TEMP
#         #print 'A:\n', H_hat_avg[:, :, M - 1]
#         #print 'B:\n', sqrtm(np.linalg.matrix_power(H_hat_avg[:, :, M - 1], 2) + 1e-6 * np.eye(p))
#         #print 'C:\n', H_hat_avg[:, :, M - 1] - sqrtm(np.linalg.matrix_power(H_hat_avg[:, :, M - 1], 2) + 1e-6 * np.eye(p))
#
#         H_bar[:, :, i] = .5 * (
#             H_hat_avg[:, :, M - 1] - sqrtm(np.linalg.matrix_power(H_hat_avg[:, :, M - 1], 2) + 1e-6 * np.eye(p))
#         )
#         # print 'H_bar[:,:,i]=',H_bar[:,:,i]
#         H_bar_avg[:, :, i] = i / (i + 1) * H_bar_avg[:, :, i - 1] + 1 / (i + 1) * H_bar[:, :, i]
#
#     Fisher = -1 * H_bar_avg[:, :, N - 1]
#     return Fisher
#
#
#
# # test the algorithm
# def log_likelihood(sigma, innovation):
#
#     # TEMPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
#     sigma = 0.1
#
#     # Gaussian likelihood
#     #print sigma, sigma**2
#     propFactor = 1 / np.sqrt(2 * np.pi * sigma**2)
#     #print 'propFactor', propFactor
#     #print 'innovation', innovation
#     ll = np.log(propFactor) + -0.5 * innovation ** 2 / sigma**2
#     #print 'll', ll
#     return ll
#
#
# def LogL_func(X, sigma_obs = .1):
#     n = 50
#     p = len(X0)
#     Z = []
#     for j in range(n):
#         Z.append(np.linalg.norm(X0 - np.ones(shape=(1, p))) + np.random.normal(0, sigma_obs))
#     meanZ = np.mean(Z)
#     stdZ = np.std(Z)
#     logL_X = []
#     zeta = np.linalg.norm(X - np.ones(shape=(1, p))) + np.random.normal(0, sigma_obs)  # fValue(X)
#     #print 'stdZ', stdZ
#     #print 'zeta - meanZ', zeta - meanZ
#     logL_X = log_likelihood(stdZ, zeta - meanZ)
#     # logL_X = np.log(likelihood(sigma_obs, np.linalg.norm(X)))
#     # for i in range(np.shape(X)[1]):
#     #    zeta = np.linalg.norm(X[:,i]-np.ones(shape=(1,p))) + np.random.normal(0,sigma_obs) #fValue(X)
#     #    logL_X.append(np.log(likelihood(stdZ, abs(zeta-meanZ))))
#     return logL_X
#
# p = 2
# global X0
# X0 = np.random.uniform(0.0, 2.0, (p, 1))
# print 'X0 =', X0
# X_min = 0
# X_max = 2
# M = 10
# N = 100
# Perturb_size = .1 * (X_max - X_min)
# Fisher = FisherInfMatrix(X0, Perturb_size, M, N)
#
# # sigma = diag(inv(Fisher))**.5
# Covariance = np.linalg.inv(Fisher)
#
# print "eigs of fisher: ", np.linalg.eigvals(Fisher)
# print "eigs of Covariance: ", np.linalg.eigvals(Covariance)
#
# #print(Covariance)
# fig3 = plt.figure('CramerRao')
# ax = plt.subplot(111)
# x, y = X0[0:2]
# plt.plot(x, y, 'g.')
# plot_cov_ellipse(Covariance, X0, nstd=1, alpha=0.6, color='green')
# plt.xlim(-1, 3)
# plt.ylim(-1, 3)
# plt.xlabel('X', fontsize=14)
# plt.ylabel('Y', fontsize=14)
#
# # Plot the LL function in the background
# x = y = np.arange(-1, 3, 0.1)
# D = len(x)
# X, Y = np.meshgrid(x, y)
#
# Xs = X.reshape( np.prod(X.shape), 1)
# Ys = Y.reshape( np.prod(Y.shape), 1)
#
# Xvec = np.concatenate((Xs, Ys), axis=1)
#
# def dummpy_fun(X, sigma_obs):
#     #print 'X in df:\n', X
#     return (X[0]-1)**2 + (X[1]-1)**2
#
# from functools import partial
# #Zs = np.apply_along_axis( partial(LogL_func, sigma_obs=0), axis=1, arr=Xvec)
# Zs = np.apply_along_axis( partial(dummpy_fun, sigma_obs=0), axis=1, arr=Xvec)
# Zmin = np.min(Zs)
# Zmax = np.max(Zs)
# CS = plt.contourf(X, Y, Zs.reshape(D,D), levels=np.linspace(Zmin, Zmax, 25), cmap='bone')
#
# plt.show()