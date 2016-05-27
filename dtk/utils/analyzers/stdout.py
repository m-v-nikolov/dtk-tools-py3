import logging

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from plot import plot_by_channel

logger = logging.getLogger(__name__)

class StdoutAnalyzer():
    def __init__(self, simIds = None):
        self.filenames = ['StdOut.txt']
        self.simIds = simIds

    def filter(self, sim_metadata):
        return lambda x: True

    def apply(self, parser):
        parser.selected_data = parser.raw_data[self.filenames[0]]

    def combine(self, parsers):
        if self.simIds:
            try:
                selected = [parsers.get(key).selected_data for key in self.simIds]
            except:
                raise Exception('Bad simulation id(s).')
        else:
            selected = [p.selected_data for p in parsers.values()]

        combined = ''.join(selected)
        self.data = combined

    def finalize(self):
        logger.info(self.data)
