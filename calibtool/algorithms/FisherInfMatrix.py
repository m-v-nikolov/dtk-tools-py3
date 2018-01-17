from __future__ import division
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from scipy.linalg import sqrtm


def perturbed_points(center, Xmin, Xmax, M=3, N=5, n=2, resolution=None):
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
    df_perturbed = pd.DataFrame(data=X_perturbed, columns=(['i(1to4)','j(1toN)','k(1toM)','run_number']+['theta']*p))

    return df_perturbed



def FisherInfMatrix(dimensionality, df_perturbed_points, df_LL_points):
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
    # LL_data = df_LL_points.as_matrix()
    # points = df_perturbed_points.as_matrix()

    rounds = df_perturbed_points['j(1toN)'].as_matrix() # j
    samples_per_round = df_perturbed_points['k(1toM)'].as_matrix() # k, points[:, 2]
    N = (max(rounds) + 1).astype(int)
    M = (max(samples_per_round) + 1).astype(int)
    n = int((np.shape(rounds)[0])/(4*M*N))

    PlusPlusPoints = df_LL_points.loc[df_LL_points['i(1to4)']==0].filter(like='theta').as_matrix() #[0:-1:4,:]
    PlusMinusPoints = df_LL_points.loc[df_LL_points['i(1to4)']==1].filter(like='theta').as_matrix() #[1:-1:4,:]
    MinusPlusPoints = df_LL_points.loc[df_LL_points['i(1to4)']==2].filter(like='theta').as_matrix() #[2:-1:4,:]
    MinusMinusPoints = df_LL_points.loc[df_LL_points['i(1to4)']==3].filter(like='theta').as_matrix() #[3:-1:4,:]

    LL_PlusPlusPoints = df_LL_points.loc[df_LL_points['i(1to4)'] == 0, 'LL'].as_matrix()
    LL_PlusMinusPoints = df_LL_points.loc[df_LL_points['i(1to4)'] == 1, 'LL'].as_matrix()
    LL_MinusPlusPoints = df_LL_points.loc[df_LL_points['i(1to4)'] == 2, 'LL'].as_matrix()
    LL_MinusMinusPoints = df_LL_points.loc[df_LL_points['i(1to4)'] == 3, 'LL'].as_matrix()

    # dimension of X
    p = dimensionality

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

        loglPP_round_i = LL_PlusPlusPoints[(i * M):((i + 1) * M)]
        loglPM_round_i = LL_PlusMinusPoints[(i * M):((i + 1) * M)]
        loglMP_round_i = LL_MinusPlusPoints[(i * M):((i + 1) * M)]
        loglMM_round_i = LL_MinusMinusPoints[(i * M):((i + 1) * M)]

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

def sample_cov_ellipse(cov, pos, num_of_pts=10):
    """
    Sample 'num_of_pts' points from the specified covariance
    matrix (`cov`).

    Parameters
    ----------
        cov : 2-D array_like, The covariance matrix (inverse of fisher matrix). It must be symmetric and positive-semidefinite for proper sampling.
        pos : 1-D array_like, The location of the center of the ellipse, Mean of the multi variate distribution
        num_of_pts : The number of sample points.

    Returns
    -------
        ndarray of the drawn samples, of shape (num_of_pts,).
    """
    return np.random.multivariate_normal(pos, cov, num_of_pts)


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
def test():
    center = np.array([0.05,-0.92,-.98])
    Xmin = np.array([-1]*3)
    Xmax = np.array([1]*3)
    # df_perturbed_points = perturbed_points(center, Xmin, Xmax)
    # print df_perturbed_points
    # df_perturbed_points.to_csv("data.csv")
    df_perturbed_points = pd.DataFrame.from_csv("data.csv")
    ll = pd.DataFrame.from_csv("LLdata.csv")
    Fisher = FisherInfMatrix(center, df_perturbed_points, ll)
    Covariance = np.linalg.inv(Fisher)

    print("eigs of fisher: ", np.linalg.eigvals(Fisher))
    print("eigs of Covariance: ", np.linalg.eigvals(Covariance))

    fig3 = plt.figure('CramerRao')
    ax = plt.subplot(111)
    x, y = center[0:2]
    plt.plot(x, y, 'g.')
    plot_cov_ellipse(Covariance[0:2,0:2], center[0:2], nstd=3, alpha=0.6, color='green')
    sample_x, sample_y = np.random.multivariate_normal(center[0:2], Covariance[0:2,0:2], 5).T
    plt.plot(sample_x, sample_y, 'x')
    plt.xlim(Xmin[0], Xmax[0])
    plt.ylim(Xmin[1], Xmax[1])
    plt.xlabel('X', fontsize=14)
    plt.ylabel('Y', fontsize=14)

    plt.show()
