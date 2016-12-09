import logging

import pandas as pd

from dtk.utils.parsers.malaria_summary import summary_channel_to_pandas

from calibtool.analyzers.BaseSummaryCalibrationAnalyzer import BaseSummaryCalibrationAnalyzer
from calibtool import LL_calculators
from calibtool.analyzers.Helpers import \
    convert_annualized, convert_to_counts, age_from_birth_cohort, aggregate_on_index

logger = logging.getLogger(__name__)


# TODO: rename as IncidenceByAgeCohortCalibAnalyzer?
# TODO: common functions into BaseCohortCalibAnalyzer, from which also PrevalenceByAge(Season)Cohort derive?
class ClinicalIncidenceByAgeCohortAnalyzer(BaseSummaryCalibrationAnalyzer):

    filenames = ['output/MalariaSummaryReport_Annual_Report.json']

    population_channel = 'Average Population by Age Bin'

    def __init__(self, site, weight=1, compare_fn=LL_calculators.gamma_poisson_pandas, **kwargs):
        super(ClinicalIncidenceByAgeCohortAnalyzer, self).__init__(site, weight, compare_fn)
        self.reference = site.get_reference_data('annual_clinical_incidence_by_age')

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
        channel_data = pd.concat([summary_channel_to_pandas(data, c)
                                  for c in (self.channel, self.population_channel)], axis=1)

        # Convert Average Population to Person Years
        person_years = convert_annualized(channel_data[self.population_channel])
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
