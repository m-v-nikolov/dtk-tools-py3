import logging
from abc import ABCMeta
import threading

import pandas as pd

from calibtool.analyzers.BaseComparisonAnalyzer import BaseComparisonAnalyzer

logger = logging.getLogger(__name__)
thread_lock = threading.Lock()


class BaseCalibrationAnalyzer(BaseComparisonAnalyzer):

    __metaclass__ = ABCMeta

    def combine(self, parsers):
        """
        Combine the simulation data into a single table for all analyzed simulations.
        """
        selected = [p.selected_data[id(self)] for p in parsers.values() if id(self) in p.selected_data]

        print selected

        # Stack selected_data from each parser, adding unique (sim_id) and shared (sample) levels to MultiIndex
        combine_levels = ['sample', 'sim_id', 'channel']
        combined = pd.concat(selected, axis=1,
                             keys=[(d.sample, d.sim_id) for d in selected],
                             names=combine_levels)

        self.data = combined.groupby(level=['sample', 'channel'], axis=1).mean()
        logger.debug('Combined data:\n%s', self.data.iloc[:10, :4])

    @staticmethod
    def join_reference(sim, ref):
        sim.columns = sim.columns.droplevel(0)  # drop sim 'sample' to match ref levels
        return pd.concat({'sim': sim, 'ref': ref}, axis=1).dropna()

    def compare(self, sample):
        """
        Assess the result per sample, in this case the likelihood
        comparison between simulation and reference data.
        """
        return self.compare_fn(self.join_reference(sample, self.reference))

    def finalize(self):
        """
        Calculate the output result for each sample.
        """
        self.result = self.data.groupby(level='sample', axis=1).apply(self.compare)
        logger.debug(self.result)

    def cache(self):
        """
        Return a cache of the minimal data required for plotting sample comparisons
        to reference comparisons. Append the reference column to the simulation sample-point data.
        """
        tmp_ref = self.reference.copy()
        tmp_ref.columns = pd.MultiIndex.from_tuples([('ref', x) for x in tmp_ref.columns])

        cache = pd.concat([self.data, tmp_ref], axis=1).dropna()
        return self.serialize(cache)  # Return in serializable format

    @staticmethod
    def serialize(df):
        """
        Put cache of simulation samples and reference into a JSON serializable format for CalibManager.IterationState
        :param df: pandas.DataFrame with MultiIndex columns (sample, channel) with final sample column = 'ref'
        :return: JSON representation of the same content

        Example:

        sample                          3                    ref
        channel    Incidents Person Years Incidents Person Years
        Age Bin
        0.5      610.199463   2546.861179     10.40           52
        1.0      1032.260204  3036.082280     35.36           52
        2.0      319.376240   6229.157240     53.20           76
        4.0      1738.556756  6939.795139    128.35          151

        Is converted into:

        {
            "samples": [
                {
                    "Age Bin": [ 0.5, 1.0, 2.0, 4.0 ],
                    "Incidents": [ 610.199463, 1032.260204, 319.376240, 1738.556756 ],
                    "Person Years": [ 2546.861179, 3036.082280, 6229.157240, 6939.795139 ]
                },
                ...
            ]
            "ref": {
                "Age Bin": [ 0.5, 1.0, 2.0, 4.0 ],
                "Incidents": [ 10.40, 35.36, 53.20, 128.35 ],
                "Person Years": [ 52, 52, 76, 151 ]
            }
        }

        """

        samples = sorted(df.columns.levels[0].tolist())
        output = {'samples': [df[sample].reset_index().to_dict(orient='list') for sample in samples if sample != 'ref']}
        if 'ref' in samples:
            output['ref'] = df['ref'].reset_index().to_dict(orient='list')
        return output
