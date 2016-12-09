import logging
from abc import ABCMeta

from calibtool.CalibSite import CalibSite
from calibtool.study_sites.site_setup_functions import config_setup_fn, summary_report_fn, site_input_eir_fn
from calibtool.analyzers.ChannelByAgeCohortAnalyzer import IncidenceByAgeCohortAnalyzer
from calibtool.analyzers.Helpers import channel_age_json_to_pandas

logger = logging.getLogger(__name__)


fine_age_bins = [
    0.08333, 0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
    11, 12, 13, 14, 15, 20, 25, 30, 40, 50, 60, 100
]


class IncidenceCalibSite(CalibSite):
    """
    An abstract class that implements the simulation setup for incidence-by-age analyses:
    - Dielmo, Senegal
    - Ndiop, Senegal
    """

    __metaclass__ = ABCMeta

    reference_dict = {
        "Average Population by Age Bin": [],
        "Age Bin": [],
        "Annual Clinical Incidence by Age Bin": []
    }

    def get_setup_functions(self):
        return [
            config_setup_fn(duration=21915),  # 60 years (with leap years)
            summary_report_fn(age_bins=fine_age_bins, interval=360),  # TODO: reconcile with 365/12 monthly EIR
            site_input_eir_fn(self.name, birth_cohort=True)
        ]

    def get_reference_data(self, reference_type):
        site_ref_type = 'annual_clinical_incidence_by_age'

        if reference_type is not site_ref_type:
            raise Exception("%s does not support %s reference_type, only %s.",
                            self.__class__.__name__, reference_type, site_ref_type)

        reference_data = channel_age_json_to_pandas(self.reference_dict, index_key='Age Bin')

        logger.debug('Reference data:\n  %s', reference_data)
        return reference_data

    def get_analyzers(self):
        return [IncidenceByAgeCohortAnalyzer(site=self)]
