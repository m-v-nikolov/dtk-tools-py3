import logging
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import cm
from calibtool.plotters.BasePlotter import BasePlotter
from calibtool.utils import StatusPoint

logger = logging.getLogger(__name__)

sns.set_style('white')


class OptimToolPlotter(BasePlotter):
    def __init__(self):
        super(OptimToolPlotter, self).__init__( False )

    def cleanup(self):
        pass

    def plot_state_evolution(self, **kwargs):
        data = kwargs.pop('data')
        all_it = data['Iteration'].astype(int)

        dynamic = data.query('Dynamic == True')
        static = data.query('Dynamic == False')

        plt.plot(all_it, data['Center'], color='k', marker=None)
        plt.plot(dynamic['Iteration'].astype(int), dynamic['Center'], 'ko', zorder=100)
        plt.plot(static['Iteration'].astype(int), static['Center'], color='0.75', marker='o', zorder=100)
        plt.plot(all_it, data['Min'], color='r')
        plt.plot(all_it, data['Max'], color='r')

        plt.margins(0.05)
        plt.autoscale(tight=False)

    def visualize(self, iteration_state):
        self.iteration_state = iteration_state
        iteration_status = self.iteration_state.status

        self.directory = self.iteration_state.iteration_directory
        self.param_names = self.iteration_state.param_names

        self.npt = self.iteration_state.next_point_algo.get_state()
        self.data = pd.DataFrame.from_dict(self.npt['data'])
        self.state = pd.DataFrame.from_dict(self.npt['state'])
        self.regression = pd.DataFrame.from_dict(self.npt['regression'])

        if iteration_status == StatusPoint.commission:
            if self.iteration_state.iteration > 0:
                self.visualize_optimtool_diagnoistics()
        elif iteration_status == StatusPoint.plot:
            self.visualize_results()
        else:
            raise Exception('Unknown stage %s' % iteration_status.name)

        ###gc.collect()


    def visualize_results(self):

        data_this_iter = self.data.set_index('Iteration').loc[self.iteration_state.iteration]

        X_center_all = self.state.pivot('Iteration', 'Parameter', 'Center')[self.param_names].values
        X_center = X_center_all[self.iteration_state.iteration]
        X_min = self.state.pivot('Iteration', 'Parameter', 'Min')[self.param_names].values
        X_max = self.state.pivot('Iteration', 'Parameter', 'Max')[self.param_names].values
        Dynamic = self.state.pivot('Iteration', 'Parameter', 'Dynamic')[self.param_names].values

        latest_results = data_this_iter['Results'].values  # Sort by sample?
        latest_fitted = data_this_iter['Fitted'].values  # Sort by sample?

        ### VIOLIN PLOTS BY ITERATION ###
        all_results = self.all_results.copy().reset_index(drop=True)#.set_index(['iteration', 'sample'])
        fig, ax = plt.subplots()
        g = sns.violinplot(x='iteration', y='total', data=all_results, ax = ax)
#, hue=None, data=res, order=None, hue_order=None, bw='scott', cut=2, scale='area', scale_hue=True, gridsize=100, width=0.8, inner='box', split=False, dodge=True, orient=None, linewidth=None, color=None, palette=None, saturation=0.75, ax=None, **kwargs))
        plt.savefig( os.path.join(self.directory, 'Optimization_Progress.pdf'))

        fig.clf()
        plt.close(fig)
        del g, ax, fig


    def visualize_optimtool_diagnoistics(self):

        prev_iter = self.iteration_state.iteration-1
        data_prev_iter = self.data.set_index('Iteration').loc[prev_iter]
        prev_results = data_prev_iter['Results'].values  # Sort by sample?
        prev_fitted = data_prev_iter['Fitted'].values  # Sort by sample?

        data_this_iter = self.data.set_index('Iteration').loc[self.iteration_state.iteration]
        #latest_samples = data_this_iter[self.param_names].values
        #D = latest_samples.shape[1]
        D = len(self.param_names)

        ### STATE EVOLUTION ###
        cw = None if D < 3 else int(np.ceil(np.sqrt(D)))
        g = sns.FacetGrid(self.state, row=None, col='Parameter', hue=None, col_wrap=cw, sharex=False, sharey=False, size=3, aspect=1, palette=None, row_order=None, col_order=None, hue_order=None, hue_kws=None, dropna=True, legend_out=True, despine=True, margin_titles=True, xlim=None, ylim=None, subplot_kws=None, gridspec_kws=None)
        g = g.map_dataframe(self.plot_state_evolution)
        g = g.set_titles(col_template='{col_name}') # , size = 15
        g.savefig( os.path.join(self.directory, 'Optimization_State_Evolution.pdf'))
        plt.close()

        # Regression based on results from previous iteration
        regression_by_iter = self.regression.pivot('Iteration', 'Parameter', 'Value')
        rsquared = regression_by_iter.loc[prev_iter, 'Rsquared']

        ### REGRESSION ###
        fig, ax = plt.subplots()
        h1 = plt.plot( prev_results, prev_fitted, 'o', figure=fig)
        h2 = plt.plot( [min(prev_results), max(prev_results)], [min(prev_results), max(prev_results)], 'r-')
        plt.xlabel('Simulation Output')
        plt.ylabel('Linear Regression')
        plt.title( rsquared )
        plt.savefig( os.path.join(self.directory, 'Optimization_Regression.pdf'))

        fig.clf()
        plt.close(fig)

        del h1, h2, ax, fig

        ### STATE ###

        dynamic_state = self.state.query('Iteration == @prev_iter & Dynamic == True')
        D_dynamic = len(dynamic_state)
        dynamic_param_names = list(dynamic_state['Parameter'].values)

        if D_dynamic == 1:
            data_sorted = data_prev_iter.sort_values(dynamic_param_names[0])

            sorted_samples = data_sorted[dynamic_param_names]
            sorted_results = data_sorted['Results']
            sorted_fitted = data_sorted['Fitted']

            fig, ax = plt.subplots()
            h1 = plt.plot( sorted_samples, sorted_results, 'ko', figure=fig)
            yl = ax.get_ylim()

            X_center = self.state.pivot('Iteration', 'Parameter', 'Center')[dynamic_param_names[0]].values[prev_iter]
            h2 = plt.plot( 2*[X_center], yl, 'b-', figure=fig)

            h3 = plt.plot( sorted_samples, sorted_fitted, 'r-', figure=fig)

            plt.title( rsquared )
            plt.xlabel(dynamic_param_names[0])
            plt.ylabel('Result')
            plt.savefig( os.path.join(self.directory, 'Optimization_Sample_Results.pdf'))

            fig.clf()
            plt.close(fig)

            del h1, h2, h3, ax, fig

        elif D_dynamic == 2:
            x0 = data_prev_iter[dynamic_param_names[0]]
            x1 = data_prev_iter[dynamic_param_names[1]]
            y = prev_results
            y_fit = prev_fitted

            rp = regression_by_iter.loc[prev_iter][['Constant'] + dynamic_param_names]#.values

            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')
            h1 = ax.scatter( x0, x1, y, c='k', marker='o', figure=fig)
            i = int(prev_iter)

            X_center = self.state.pivot('Iteration', 'Parameter', 'Center')[dynamic_param_names].values[prev_iter]

            h2 = ax.scatter( X_center[0], 
                        X_center[1], 
                        rp[0] + rp[1]*X_center[0] + rp[2]*X_center[1],
                        c='b', marker='.', s=200, figure=fig)

            '''
            h3 = ax.plot(    [xc[0] for xc in X_center_all[i:i+2]],
                        [xc[1] for xc in X_center_all[i:i+2]], 
                        [
                            rp[0] + rp[1]*X_center_all[i][0] + rp[2]*X_center_all[i][1],
                            rp[0] + rp[1]*X_center_all[i+1][0] + rp[2]*X_center_all[i+1][1]
                        ], c='b', figure=fig)
            '''

            h4 = ax.scatter( x0, x1, y_fit, c='r', marker='d', figure=fig)

            xl = ax.get_xlim()
            yl = ax.get_ylim()

            x_surf=np.linspace(xl[0], xl[1], 25)                # generate a mesh
            y_surf=np.linspace(yl[0], yl[1], 25)
            x_surf, y_surf = np.meshgrid(x_surf, y_surf)
            z_surf = rp[0] + rp[1]*x_surf + rp[2]*y_surf
            h5 = ax.plot_surface(x_surf, y_surf, z_surf, cmap=cm.hot, rstride=1, cstride=1,
                linewidth=0, antialiased=True, edgecolor=(0,0,0,0), alpha=0.5)

            h6 = plt.contour(x_surf, y_surf, z_surf, 10,
                  #[-1, -0.1, 0, 0.1],
                  alpha=0.5,
                  cmap=plt.cm.bone)


            plt.title( rsquared )

            ax.set_xlabel(dynamic_param_names[0])
            ax.set_ylabel(dynamic_param_names[1])
            ax.set_zlabel('Result')

            plt.savefig( os.path.join(self.directory, 'Optimization_Sample_Results.pdf'))

            fig.clf()
            plt.close(fig)

            del h1, h2, h4, h5, h6, ax, fig # h3


    def cleanup_plot(self, calib_manager):
        pass
