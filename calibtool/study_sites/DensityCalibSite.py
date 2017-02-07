import logging
from collections import OrderedDict
from abc import ABCMeta

from calibtool.CalibSite import CalibSite
from calibtool.study_sites.site_setup_functions import \
    config_setup_fn, summary_report_fn, add_treatment_fn, site_input_eir_fn
from calibtool.analyzers.ChannelBySeasonAgeDensityCohortAnalyzer import ChannelBySeasonAgeDensityCohortAnalyzer
from calibtool.analyzers.Helpers import season_channel_age_density_json_to_pandas,\
    season_channel_age_density_csv_to_pandas

logger = logging.getLogger(__name__)


class DensityCalibSite(CalibSite):
    """
    An abstract class that implements the simulation setup for density-by-season-and-age analyses:
    - Laye, Burkina Faso
    - Dapelogo, Burkina Faso
    """

    __metaclass__ = ABCMeta

    metadata = {
        'parasitemia_bins': [],
        'age_bins': [],
        'seasons_by_month': {}
    }

    reference_dict = {}

    reference_csv = {}

    def get_setup_functions(self):
        return [
            config_setup_fn(duration=21915),  # 60 years (with leap years)
            summary_report_fn(interval=30, description='Monthly_Report'),  # TODO: reconcile with 365/12 monthly EIR
            add_treatment_fn(),
            site_input_eir_fn(self.name, birth_cohort=True)
        ]

    def get_reference_data(self, reference_type):
        site_ref_type = 'density_by_age_and_season'

        if reference_type is not site_ref_type:
            raise Exception("%s does not support %s reference_type, only %s.",
                            self.__class__.__name__, reference_type, site_ref_type)


        if bool(self.reference_csv):
            reference_data = season_channel_age_density_csv_to_pandas(self.reference_csv, self.metadata)
        elif bool(self.reference_dict):
            reference_bins = OrderedDict([
                ('Age Bin', self.metadata['age_bins']),
                ('PfPR Bin', self.metadata['parasitemia_bins'])
            ])
            reference_data = season_channel_age_density_json_to_pandas(self.reference_dict, reference_bins)

        logger.debug('Reference data:\n  %s', reference_data)
        return reference_data

    def get_analyzers(self):
        return [ChannelBySeasonAgeDensityCohortAnalyzer(site=self, seasons=self.metadata['seasons_by_month'])]
