import logging
from abc import ABCMeta

from calibtool.CalibSite import CalibSite
from calibtool.study_sites.site_setup_functions import \
    vector_stats_report_fn
from calibtool.analyzers.ChannelByMonthSpatialIncidenceAnalyzer import ChannelByMonthSpatialIncidenceAnalyzer


logger = logging.getLogger(__name__)


class IncidenceSpatialCalibSite(CalibSite):
    """
    An abstract class that implements the simulation setup for density-by-season-and-age analyses:
    - Laye, Burkina Faso
    - Dapelogo, Burkina Faso
    """

    __metaclass__ = ABCMeta

    metadata = {
        'months': {}
    }

    def get_setup_functions(self):
        return [
            vector_stats_report_fn()
        ]

    def get_reference_data(self, reference_type):
        site_ref_type = 'cc_by_month'

        if reference_type is not site_ref_type:
            raise Exception("%s does not support %s reference_type, only %s.",
                            self.__class__.__name__, reference_type, site_ref_type)

    def get_analyzers(self):
        return [ChannelByMonthSpatialIncidenceAnalyzer(site=self, seasons=self.metadata['months'])]
