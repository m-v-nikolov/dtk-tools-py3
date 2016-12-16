import logging
from abc import ABCMeta, abstractmethod

import pandas as pd
import numpy as np

from dtk.utils.parsers.malaria_summary import summary_channel_to_pandas

from calibtool.analyzers.BaseSummaryCalibrationAnalyzer import BaseSummaryCalibrationAnalyzer
from calibtool.LL_calculators import gamma_poisson_pandas, beta_binomial_pandas
from calibtool.analyzers.Helpers import \
    convert_annualized, convert_to_counts, age_from_birth_cohort, aggregate_on_index

logger = logging.getLogger(__name__)


class ChannelByAgeCohortAnalyzer(BaseSummaryCalibrationAnalyzer):
    """
    Base class implementation for similar comparisons of age-binned reference data to simulation output.
    """

    __metaclass__ = ABCMeta

    filenames = ['output/MalariaSummaryReport_Annual_Report.json']
    population_channel = 'Average Population by Age Bin'

    site_ref_type = None

    @abstractmethod
    def __init__(self, site, weight=1, compare_fn=None, **kwargs):
        super(ChannelByAgeCohortAnalyzer, self).__init__(site, weight, compare_fn)
        self.reference = site.get_reference_data(self.site_ref_type)

        ref_channels = self.reference.columns.tolist()
        if len(ref_channels) != 2:
            raise Exception('Expecting two channels from reference data: %s' % ref_channels)
        try:
            ref_channels.pop(ref_channels.index(self.population_channel))
            self.channel = ref_channels[0]
        except ValueError:
            raise Exception('Population channel (%s) missing from reference data: %s' %
                            (self.population_channel, ref_channels))

        # Convert reference columns to those needed for likelihood comparison
        # TODO: "Counts" or "Observations"  more generic than "Incidents"?
        self.reference = pd.DataFrame({'Person Years': self.reference[self.population_channel],
                                       'Incidents': (self.reference[self.population_channel]
                                                     * self.reference[self.channel])})

    def apply(self, parser):
        """
        Extract data from output data and accumulate in same bins as reference.
        """

        # Load data from simulation
        data = parser.raw_data[self.filenames[0]]

        # Get channels by age and time series
        channel_series = summary_channel_to_pandas(data, self.channel)
        population_series = summary_channel_to_pandas(data, self.population_channel)
        channel_data = pd.concat([channel_series, population_series], axis=1)

        # Convert Average Population to Person Years
        person_years = convert_annualized(channel_data[self.population_channel],
                                          start_day=channel_series.Start_Day,
                                          reporting_interval=channel_series.Reporting_Interval)
        channel_data['Person Years'] = person_years

        # Calculate Incidents from Annual Incidence and Person Years
        channel_data['Incidents'] = convert_to_counts(channel_data[self.channel], channel_data['Person Years'])

        # Reset multi-index and perform transformations on index columns
        df = channel_data.reset_index()
        df = age_from_birth_cohort(df)  # calculate age from time for birth cohort

        # Re-bin according to reference and return single-channel Series
        sim_data = aggregate_on_index(df, self.reference.index, keep=['Incidents', 'Person Years'])

        sim_data.sample = parser.sim_data.get('__sample_index__')
        sim_data.sim_id = parser.sim_id

        return sim_data

    @classmethod
    def plot_comparison(cls, fig, data, **kwargs):
        ax = fig.gca()
        df = pd.DataFrame.from_dict(data, orient='columns')
        incidence = df['Incidents'] / df['Person Years']
        age_bin_left_edges = [0] + df['Age Bin'][:-1].tolist()
        age_bin_centers = 0.5 * (df['Age Bin'] + age_bin_left_edges)
        if kwargs.pop('reference', False):
            # TODO: override with binomial error in derived prevalence analyzer class
            incidence_err = (np.sqrt(df['Incidents']) / df['Person Years']).tolist()
            ax.errorbar(age_bin_centers, incidence, yerr=incidence_err, **kwargs)
        else:
            fmt_str = kwargs.pop('fmt', None)
            args = (fmt_str,) if fmt_str else ()
            ax.plot(age_bin_centers, incidence, *args, **kwargs)
        ax.set(xlabel='Age (years)', ylabel=cls.site_ref_type.replace('_by_age', '').replace('_', ' ').title())


class PrevalenceByAgeCohortAnalyzer(ChannelByAgeCohortAnalyzer):
    """
    Compare reference prevalence-by-age measurements to simulation output.

    N.B. Using the logic that converts annualized incidence and average populations to incidents and person years,
         implicitly introduces a 1-year time constant for correlations in repeat prevalence measurements.
    """

    site_ref_type = 'prevalence_by_age'

    def __init__(self, site, weight=1, compare_fn=beta_binomial_pandas, **kwargs):
        super(PrevalenceByAgeCohortAnalyzer, self).__init__(site, weight, compare_fn, **kwargs)


class IncidenceByAgeCohortAnalyzer(ChannelByAgeCohortAnalyzer):
    """
    Compare reference incidence-by-age measurements to simulation output.
    """

    site_ref_type = 'annual_clinical_incidence_by_age'

    def __init__(self, site, weight=1, compare_fn=gamma_poisson_pandas, **kwargs):
        super(IncidenceByAgeCohortAnalyzer, self).__init__(site, weight, compare_fn, **kwargs)

