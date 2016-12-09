import logging
from abc import ABCMeta

import pandas as pd

from calibtool.analyzers.BaseComparisonAnalyzer import BaseComparisonAnalyzer

logger = logging.getLogger(__name__)


class BaseSummaryCalibrationAnalyzer(BaseComparisonAnalyzer):

    __metaclass__ = ABCMeta

    def combine(self, parsers):
        """
        Combine the simulation data into a single table for all analyzed simulations.
        """

        selected = [p.selected_data[id(self)] for p in parsers.values() if id(self) in p.selected_data]

        # Stack selected_data from each parser, adding unique (sim_id) and shared (sample) levels to MultiIndex
        combine_levels = ['sample', 'sim_id', 'channel']
        combined = pd.concat(selected, axis=1,
                             keys=[(d.sample, d.sim_id) for d in selected],
                             names=combine_levels)

        self.data = combined.groupby(level=['sample', 'channel'], axis=1).mean()
        logger.debug(self.data)

    @staticmethod
    def join_reference(sim, ref):
        # TODO: use pattern from cache() and rename sample to 'sim' in compare()?
        sim.columns = sim.columns.droplevel(0)  # drop sim_id to match ref levels
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
        return cache
