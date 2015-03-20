import os
import warnings
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.cm as cm
from matplotlib.widgets import Button

# a class to analyze MalariaPatient json output
class MalariaPatientAnalyzer():

    def __init__(self, filename='PolioSurveyJSONAnalyzer_Day0_0.json'):
        self.filenames = [filename]
        self.data = {}
        self.ntsteps = 0

    def filter(self, sim_metadata):
        return True

    def map(self, output_data):
        return output_data

    def reduce(self, parsers):
        if len(parsers) > 1:
            warnings.warn("MalariaPatientDisplayer analyzer only supports a single simulation. Defaulting to first simulation of sweep.", RuntimeWarning)
        self.data = parsers.values()[0].output_data[self.filenames[0]]['patient_array']
        self.ntsteps = parsers.values()[0].output_data[self.filenames[0]]['ntsteps']

    def plot_hist(self, s, data, ymax=6, orientation='vertical', color='b'):
        s.clear()
        s.hist(data, np.arange(-2,ymax,0.5), alpha=0.2, color=color, orientation=orientation)
        if orientation == 'vertical':
            s.get_xaxis().set_ticklabels([])
            s.locator_params(axis='y', tight=True, nbins=4)
        else:
            s.get_yaxis().set_ticklabels([])
            s.locator_params(axis='x', tight=True, nbins=4)

    def finalize(self):
        tstep=0
        par=[]
        gam=[]
        cat=[]
        for t in range(self.ntsteps):
            aa=[]
            gg=[]
            cc=[]
            for p in self.data:
                a=p['true_asexual_parasites']
                g=p['true_gametocytes']
                f=p['temps']
                r=p['rdt']
                aa.append(np.nan if t>=len(a) else np.log10(a[t]) if a[t] > 1e-2 else -2)
                gg.append(np.nan if t>=len(g) else np.log10(g[t]) if g[t] > 1e-2 else -2)
                cc.append(0 if t>=len(f) else (f[t]-37) if f[t] > 38.5 else -1 if r[t]==0 else -2 if g[t]==0 else 0) # categorize: infected, detected, symptoms
            par.append(aa)
            gam.append(gg)
            cat.append(cc)

        fig, ax = plt.subplots(figsize=(8,6))
        fig.subplots_adjust(left=0.1, bottom=0.05, top=0.9, right=0.95)
        gs = gridspec.GridSpec(2,2,width_ratios=[4,1],height_ratios=[4,1])

        txt = fig.text(0.38, 0.9, 'Day %d' % tstep, fontweight='bold')

        ax1=plt.subplot(gs[0])
        scat1=plt.scatter(par[tstep], gam[tstep], c=cat[tstep], s=60, alpha=0.2, cmap=cm.jet, vmin=-1, vmax=3);
        plt.xlim([-2.3,6])
        plt.ylim([-2.3,5])
        plt.ylabel('log10 gametocytes', fontweight='bold')
        plt.xlabel('log10 asexual parasites', fontweight='bold')

        ax2=plt.subplot(gs[1])
        hgam=self.plot_hist(ax2, gam[tstep], ymax=5, orientation='horizontal', color='g')

        ax3=plt.subplot(gs[2])
        hpar=self.plot_hist(ax3, par[tstep])

        def redraw(tstep):
            txt.set_text('Day %d' % tstep)
            #print(tstep,par[tstep],gam[tstep],fev[tstep])
            scat1.set_offsets(zip(par[tstep],gam[tstep]))
            scat1.set_array(np.array(cat[tstep]))

            hgam=self.plot_hist(ax2, gam[tstep], ymax=5, orientation='horizontal', color='g')
            hpar=self.plot_hist(ax3, par[tstep])

            fig.canvas.draw()

        class Index:
            def __init__(self, tsteps):
                self.tstep = 0
                self.ntsteps = tsteps
            
            def minus_day(self, event):
                self.tstep = self.tstep-1 if self.tstep > 1 else self.tstep
                redraw(self.tstep)

            def plus_day(self, event):
                self.tstep = self.tstep+1 if self.tstep < self.ntsteps-1 else self.tstep
                redraw(self.tstep)

            def plus_week(self, event):
                self.tstep = self.tstep+7 if self.tstep < self.ntsteps-7 else self.ntsteps-1
                redraw(self.tstep)

            def minus_week(self, event):
                self.tstep = self.tstep-7 if self.tstep > 7 else 0
                redraw(self.tstep)

            def plus_month(self, event):
                self.tstep = self.tstep+30 if self.tstep < self.ntsteps-30 else self.ntsteps-1
                redraw(self.tstep)

            def minus_month(self, event):
                self.tstep = self.tstep-30 if self.tstep > 30 else 0
                redraw(self.tstep)

        callback = Index(self.ntsteps)

        axjumpbk = plt.axes([0.13, 0.89, 0.06, 0.04])
        axskipbk = plt.axes([0.19, 0.89, 0.06, 0.04])
        axprev = plt.axes([0.25, 0.89, 0.06, 0.04])
        axnext = plt.axes([0.53, 0.89, 0.06, 0.04])
        axskip = plt.axes([0.59, 0.89, 0.06, 0.04])
        axjump = plt.axes([0.65, 0.89, 0.06, 0.04])

        bnext = Button(axnext, '>')
        bnext.on_clicked(callback.plus_day)

        bprev = Button(axprev, '<')
        bprev.on_clicked(callback.minus_day)

        bskip = Button(axskip, '>>')
        bskip.on_clicked(callback.plus_week)

        bskipbk = Button(axskipbk, '<<')
        bskipbk.on_clicked(callback.minus_week)

        bjump = Button(axjump, '>>>')
        bjump.on_clicked(callback.plus_month)

        bjumpbk = Button(axjumpbk, '<<<')
        bjumpbk.on_clicked(callback.minus_month)

        plt.tight_layout()
        plt.show() # required to be here?

