import math
import time

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import multivariate_normal
from scipy.spatial.distance import seuclidean

import logging
logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# TODO: generalize interfaces and patterns after port
#       - run DTK, BarcodeModel, DiseaseModel inside iteration loop
#       - flexible next-point for different calib algo, separatrix, filtering
#       - maintain flexibility of LOCAL/HPC-OLD/HPC (refactor SimulationManager and/or dtk.py commandline with some polymorphism?)

class IMIS:
    '''
    IMIS algorithm ported from R code:
    http://cran.r-project.org/web/packages/IMIS
    '''
    def __init__(self, prior_fn, likelihood_fn=[],
                   n_initial_samples=1e4, n_samples_per_iteration=1e3,
                   n_iterations=100, n_resamples=3e3, curr_status={}, initial_samples=[]):

        self.prior_fn=prior_fn
        self.likelihood_fn=likelihood_fn
        self.debug_plots_fn=[]

        self.n_initial_samples=int(n_initial_samples)             # B0 = 10*B
        self.n_samples_per_iteration=int(n_samples_per_iteration) # B
        self.n_iterations=int(n_iterations)                       # number_k

        self.n_resamples=n_resamples                              # B.re

        self.likelihoods=[]                                   # like_all
        self.priors=[]                                        # prior_all
        self.gaussian_probs=[]                                # gaussian_all
        self.gaussian_centers=[]                              # center_all
        self.gaussian_covariances=[]                          # sigma_all
        if initial_samples == [] :
            self.samples=self.draw_initial_samples()              # X_all
        else :
            self.samples=initial_samples
        self.latest_samples=self.samples[:]                   # X_k

        if curr_status != {} :
            self.likelihoods=curr_status['likelihoods']
            self.priors=curr_status['priors']
            self.gaussian_probs=curr_status['gaussian_probs']
            self.gaussian_centers=curr_status['gaussian_centers']
            self.gaussian_covariances=curr_status['gaussian_covariances']
            self.samples=curr_status['samples']
            self.latest_samples=curr_status['latest_samples']

        self.sampling_envelope=[]                             # envelop_all
        self.weights=[]
        self.resamples=[]                                     # resample_X
            

        self.D=1 # optimizer not implemented

        logger.info('IMIS instance with %d initial samples, %d per iteration, %d iterations, %d resamples' % 
                    (self.n_initial_samples,self.n_samples_per_iteration,self.n_iterations,self.n_resamples))


        self.n_dimensions=self.samples[0].size
        logger.info('IMIS calibration dimensions = %d'%self.n_dimensions)

        self.iteration=0

    @classmethod
    def from_iteration_num(cls, iteration, IMIS_settings, curr_status={}, initial_samples=[]) :

        return cls(IMIS_settings['prior_fn'], 
                   n_initial_samples=IMIS_settings['n_initial_samples'],
                   n_samples_per_iteration=IMIS_settings['n_samples_per_iteration'],
                   n_iterations=IMIS_settings['n_iterations'],
                   n_resamples=IMIS_settings['n_resamples'], curr_status=curr_status, initial_samples=initial_samples)

    def draw_initial_samples(self):
        initial_samples=self.sample_from_function(self.prior_fn,self.n_initial_samples)
        logger.debug('Initial samples:\n%s' % initial_samples)
        self.prior_covariance = np.cov(initial_samples.T)
        logger.debug('Covariance of prior samples:\n%s' % self.prior_covariance)
        return initial_samples

    def sample_from_function(self,function,N):
        return np.array([function.rvs() for i in range(N)])

    def run(self):
        for iteration in range(self.n_iterations):
            end_condition = self.run_iteration(iteration)
            if end_condition: break
        self.resamples,self.resample_weights=self.resample()

    def resample(self):
        nonzero_idxs=self.weights > 0
        idxs=[i for i,w in enumerate(self.weights[nonzero_idxs])]
        resample_idxs=np.random.choice(idxs,self.n_resamples,replace=True,p=self.weights[nonzero_idxs])
        return self.samples[resample_idxs],self.weights[resample_idxs]

    def run_iteration(self,iteration):
        self.set_likelihoods(self.calculate_sample_likelihoods(self.latest_samples))
        logger.debug('Likelihoods:\n%s' % self.likelihoods)
        return self.update(iteration)

    def set_likelihoods(self,likelihoods):
        self.likelihoods.extend(likelihoods)
        logger.debug('Likelihoods:\n%s' % self.likelihoods)

    def get_next_samples(self):
        return self.latest_samples

    def update(self,iteration):

        self.iteration=iteration
        logger.info('ITERATION %d:' % iteration)

        self.priors.extend(self.prior_fn.pdf(self.latest_samples))
        logger.debug('Priors:\n%s' % self.priors)

        if not iteration :
            self.sampling_envelope=self.priors
        else:
            w = self.n_initial_samples/self.n_samples_per_iteration
            stack = np.vstack([[np.multiply(self.priors,w)], self.gaussian_probs])
            logger.debug('Stack weighted prior + gaussian sample prob %s:\n%s'%(stack.shape,stack))
            norm = (w+self.D+(iteration-2))
            self.sampling_envelope = np.sum(stack,0) / norm
        logger.debug('Sampling envelope:\n%s' % self.sampling_envelope)

        self.weights = [p*l/e for (p,l,e) in zip(self.priors,self.likelihoods,self.sampling_envelope)] # TODO: perform in log space
        self.weights /= np.sum(self.weights)
        logger.debug('Weights:\n%s' % self.weights)

        if self.debug_plots_fn:
            self.debug_plots_fn(self)

        max_weight_idx = np.argmax(self.weights)
        important_sample = self.samples[max_weight_idx]
        logger.debug('Centering new points at:\n%s' % important_sample)
        self.gaussian_centers.append(important_sample)

        V=self.prior_covariance if self.prior_covariance.size==1 else np.diag(self.prior_covariance)
        distances=[seuclidean(s,important_sample,V=V) for s in self.samples] # normalized Euclid instead of mahalanobis if we're just going to diagonalize anyways
        logger.debug('Distances:\n%s'%distances)

        n_closest_idxs=np.argsort(distances)[:self.n_samples_per_iteration]
        n_closest_weights=self.weights[n_closest_idxs]
        n_closest_samples=self.samples[n_closest_idxs]
        logger.debug('N-closest samples:\n%s'%n_closest_samples)
        logger.debug('N-closest weights:\n%s'%n_closest_weights)
        weighted_covariance=self.calculate_weighted_covariance(n_closest_samples,weights=n_closest_weights+1./len(self.weights),center=important_sample)
        self.gaussian_covariances.append(weighted_covariance)

        mvn=multivariate_normal( mean=important_sample, cov=weighted_covariance )
        t=self.sample_from_function(mvn,self.n_samples_per_iteration)
        while True :
            p=self.prior_fn.pdf(t)
            if all([x > 0 for x in p]) : break
            n_invalid = len(filter(lambda(x): x == 0, p))
            t=np.concatenate(([y.tolist() for i, y in enumerate(t) if p[i] > 0],self.sample_from_function(mvn,n_invalid)))#,axis=1 if self.n_dimensions==1 else 0)
        if self.n_dimensions==1 :
            t=np.array([t.tolist()]).T
        self.latest_samples=t
        logger.debug('Next samples:\n%s'%self.latest_samples)
        self.samples=np.concatenate((self.samples,self.latest_samples))#,axis=1 if self.n_dimensions==1 else 0)
        logger.debug('All samples:\n%s'%self.samples)

        if not iteration :
            self.gaussian_probs=multivariate_normal.pdf(self.samples,important_sample,weighted_covariance).reshape((1,len(self.samples)))
        else:
            updated_gaussian_probs=np.zeros(((self.D+iteration),len(self.samples)))
            updated_gaussian_probs[:self.gaussian_probs.shape[0],:self.gaussian_probs.shape[1]]=self.gaussian_probs
            for j in range(iteration):
                updated_gaussian_probs[j,self.gaussian_probs.shape[1]:]=multivariate_normal.pdf(self.latest_samples,self.gaussian_centers[j],self.gaussian_covariances[j])
            updated_gaussian_probs[-1:]=multivariate_normal.pdf(self.samples,important_sample,weighted_covariance)
            self.gaussian_probs=updated_gaussian_probs
        logger.debug('Gaussian sample probabilities %s:\n%s'%(self.gaussian_probs.shape,self.gaussian_probs))

        weight_distribution=np.sum(1-(1-np.array(self.weights))**self.n_resamples)
        end_condition=(1-np.exp(-1))*self.n_resamples
        if weight_distribution > end_condition:
            logger.info('Truncating IMIS iteration: %0.2f > %0.2f' % (weight_distribution,end_condition))
            return True
        else:
            logger.info('Continuing IMIS iterations: %0.2f < %0.2f' % (weight_distribution,end_condition))
            return False

    def calculate_sample_likelihoods(self,samples):
        return self.likelihood_fn(samples)

    def calculate_weighted_covariance(self,samples,weights,center):
        d=samples-center
        if self.n_dimensions==1:
            w=weights/sum(weights)
            #d2=np.square(d)
            d2=np.array([x[0] for x in np.square(d)])
            sig2=np.dot(d2,w)
        else:
            weights=weights/sum(weights) #inside R function (cov.wt) these are normalized
            w=1./(1-sum(np.square(weights)))
            wd=np.multiply(d.T,weights).T
            sig2=w*np.dot(wd.T,d)
        logger.debug('Weighted covariance:\n%s'%sig2)
        return sig2

    def get_current_state(self) :
        t = {}
        t['priors'] = self.priors
        t['samples'] = self.samples
        t['gaussian_probs'] = self.gaussian_probs
        t['gaussian_centers'] = self.gaussian_centers
        t['gaussian_covariances'] = self.gaussian_covariances
        t['likelihoods'] = self.likelihoods
        t['latest_samples'] = self.latest_samples
        return t

def test_multivariate():
    likelihood_fn = lambda x: multivariate_normal( mean=[1,1], cov=[[1,0.6],[0.6,1]] ).pdf(x)
    prior_fn = multivariate_normal( mean=[0,0], cov=3*np.identity(2) )

    x, y = np.mgrid[-5:5:.01, -5:5:.01]
    pos = np.empty(x.shape + (2,))
    pos[:, :, 0] = x; pos[:, :, 1] = y
    l=likelihood_fn(pos)*prior_fn.pdf(pos)

    def compare_samples_to_likelihood(imis):
        f, (ax1, ax2, ax3) = plt.subplots(1, 3, sharey=True,sharex=True,num='Iteration %d'%imis.iteration,figsize=(14,5))

        ax1.scatter(*zip(*imis.samples),c='navy',alpha=0.2,lw=0)
        if imis.iteration: ax1.scatter(*zip(*imis.latest_samples),c='firebrick',alpha=0.2,lw=0)
        ax1.contour(x, y, l, cmap='Reds')
        ax1.set_title('Samples')

        ax2.scatter(*zip(*imis.samples),c=imis.weights,cmap='jet',alpha=0.2,lw=0)
        ax2.contour(x, y, l, cmap='Reds')
        ax2.set_title('Weights')

        ax3.scatter(*zip(*imis.samples),c=imis.likelihoods,cmap='jet',alpha=0.2,lw=0)
        ax3.contour(x, y, l, cmap='Reds')
        ax3.set_title('Likelihoods')

        plt.tight_layout()

    imis=IMIS(prior_fn,likelihood_fn,n_initial_samples=5000,n_samples_per_iteration=500)
    #imis.debug_plots_fn=compare_samples_to_likelihood
    result=imis.run()

    plt.figure('Final',figsize=(11,5))
    plt.subplot(121)
    plt.hist(imis.weights,bins=50,alpha=0.3)
    plt.hist(imis.resample_weights,bins=50,alpha=0.3,color='firebrick')
    plt.title('Weights')
    plt.subplot(122)
    plt.hexbin(*zip(*imis.resamples),gridsize=50,cmap='Blues',mincnt=0.01)
    plt.contour(x, y, l, cmap='Reds')
    plt.xlim([-2,3])
    plt.ylim([-2,3])
    plt.title('Resamples')
    plt.tight_layout()

def test_univariate():
    likelihood_fn = lambda xx: [np.exp(-1*np.sin(3*x)*np.sin(x**2) - 0.1*x**2) for x in xx]
    prior_fn = multivariate_normal( mean=[0], cov=[5**2] )
    imis=IMIS(prior_fn,likelihood_fn,n_initial_samples=5000,n_samples_per_iteration=500)
    result=imis.run()
    plt.figure('Final',figsize=(10,5))
    xx=np.arange(-5,5,0.01)
    plt.plot(xx,prior_fn.pdf(xx),'navy',label='Prior')
    plt.plot(xx,np.multiply(likelihood_fn(xx),prior_fn.pdf(xx)),'r',label='Posterior')
    plt.hist(imis.resamples,bins=100,alpha=0.3,label='Resamples',normed=True)
    plt.xlim([-5,5])
    plt.legend()
    plt.tight_layout()

def test_sim_loop():
    likelihood_fn = lambda xx: [np.exp(-1*np.sin(3*x)*np.sin(x**2) - 0.1*x**2) for x in xx]
    prior_fn = multivariate_normal( mean=[0], cov=[5**2] )
    imis=IMIS(prior_fn,likelihood_fn=[],n_initial_samples=5000,n_samples_per_iteration=500)

    def run_sims(next_samples):
        logger.info('Pretending to run simulations and wait for them to be finished...')
        time.sleep(2)
        return True

    def calculate_likelihoods(next_samples):
        return likelihood_fn(next_samples)

    for iteration in range(imis.n_iterations):
        next_samples=imis.get_next_samples()
        run_sims(next_samples)
        next_likelihoods=calculate_likelihoods(next_samples)
        imis.set_likelihoods(next_likelihoods)
        finished = imis.update(iteration)
        if finished: break
    resamples,resample_weights=imis.resample()

    pltxs.figure('Final',figsize=(10,5))
    xx=np.arange(-5,5,0.01)
    plt.plot(xx,prior_fn.pdf(xx),'navy',label='Prior')
    plt.plot(xx,np.multiply(likelihood_fn(xx),prior_fn.pdf(xx)),'r',label='Posterior')
    plt.hist(resamples,bins=100,alpha=0.3,label='Resamples',normed=True)
    plt.xlim([-5,5])
    plt.legend()
    plt.tight_layout()

if __name__ == '__main__':
    #test_univariate()
    #test_multivariate()
    test_sim_loop()
    plt.show()
