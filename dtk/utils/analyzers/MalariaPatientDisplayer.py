import os
import warnings
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

# a class to pass MalariaPatient output to GUI
class MalariaPatientDisplayer():

    def __init__(self, filename='MalariaPatientReport.json'):
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

    def get_treatments(self, patient):
        if 'treatment' not in patient:
            return[]
        else:
            return [(i,s) for (i,s) in enumerate(patient['treatment']) if s]

    def finalize(self):
        patient = self.data[-1]
        #print(patient.keys())

        fig, ax = plt.subplots(figsize=(15,6))
        fig.subplots_adjust(left=0.25, bottom=0.1, top=0.95, right=0.97)

        txt = fig.text(0.04, 0.7, 'Patient ID=%d\nAge=%d' % (0, np.floor(patient['initial_age']/365)))

        s1 = plt.subplot(211)
        tbars = plt.bar(np.arange(len(patient['temps'])), patient['temps'], width=0.8, color='#eecc99')
        plt.ylim([37, 42])
        plt.xlim([0,150])
        plt.ylabel('Fever [C]')

        treatments = self.get_treatments(patient)
        for (day,drug) in treatments:
            plt.plot([day]*2, [37,42], color='#aaaaaa')
            plt.text(day+1, 41, drug, color='#888888')

        s2 = plt.subplot(212)
        aline, = plt.semilogy(patient['asexual_parasites'], 'b-')
        gline, = plt.semilogy(patient['gametocytes'],'g-')
        plt.ylim([2, 2e6])
        plt.xlim([0,150])
        plt.ylabel('Parasite density [1/uL]');

        for (day,drug) in treatments:
            plt.plot([day]*2, [2, 2e6], color='#aaaaaa')

        def redraw(idx):
            patient = self.data[idx]
            txt.set_text('Patient ID=%d\nAge=%d' % (idx, np.floor(patient['initial_age']/365))) 
            aline.set_xdata(np.arange(len(patient['asexual_parasites'])))
            aline.set_ydata(patient['asexual_parasites'])
            gline.set_xdata(np.arange(len(patient['gametocytes'])))
            gline.set_ydata(patient['gametocytes'])

            treatments = self.get_treatments(patient)
            for ii in range(len(s2.lines)-1,1,-1): # pop off all lines except the first two (gametocytes,parasites)
                s2.lines.pop(ii)
            for (day,drug) in treatments:
                s2.plot([day]*2, [2, 2e6], color='#aaaaaa')

            s1.cla()
            s1.bar(np.arange(len(patient['temps'])), patient['temps'], width=0.8, color='#eecc99')
            s1.set_ylim([37, 42])
            s1.set_xlim([0,150])
            s1.set_ylabel('Fever [C]')
            for (day,drug) in treatments:
                s1.plot([day]*2, [37,42], color='#aaaaaa')
                s1.text(day+1, 41, drug, color='#888888')
            fig.canvas.draw()

        class Index:
            def __init__(self, npatients):
                self.idx = 0
                self.npatients = npatients
            
            def prev(self, event):
                self.idx = self.idx-1 if self.idx > 1 else self.idx
                redraw(self.idx)

            def next(self, event):
                self.idx = self.idx+1 if self.idx < self.npatients-1 else self.idx
                redraw(self.idx)

        callback = Index(len(self.data))
        axprev = plt.axes([0.03, 0.3, 0.15, 0.075])
        axnext = plt.axes([0.03, 0.4, 0.15, 0.075])

        bnext = Button(axnext, '------ NEXT ----->')
        bnext.on_clicked(callback.next)

        bprev = Button(axprev, '<-- PREVIOUS ---')
        bprev.on_clicked(callback.prev)

        plt.show() # required to be here?

