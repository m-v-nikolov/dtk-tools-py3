import logging
from abc import ABCMeta

from calibtool.CalibSite import CalibSite
from calibtool.study_sites.site_setup_functions import \
    config_setup_fn, summary_report_fn, add_treatment_fn, site_input_eir_fn
from calibtool.analyzers.ChannelBySeasonAgeDensityCohortAnalyzer import ChannelBySeasonAgeDensityCohortAnalyzer


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

    def get_analyzers(self):
        return [ChannelBySeasonAgeDensityCohortAnalyzer(site=self, seasons=self.metadata['seasons_by_month'])]
