import logging
from abc import ABCMeta

from calibtool.CalibSite import CalibSite
from calibtool.study_sites.site_setup_functions import \
    vector_stats_report_fn
<<<<<<< HEAD
<<<<<<< HEAD
from calibtool.analyzers.ChannelBySeasonSpatialCohortAnalyzer import ChannelBySeasonSpatialCohortAnalyzer
=======
from calibtool.analyzers.ChannelBySeasonCohortAnalyzer import ChannelBySeasonCohortAnalyzer
>>>>>>> Small changes to spatial manager files
=======
from calibtool.analyzers.ChannelBySeasonSpatialCohortAnalyzer import ChannelBySeasonSpatialCohortAnalyzer
>>>>>>> Updated spatial analyzer and spatial entomology calib site


logger = logging.getLogger(__name__)


class EntomologySpatialCalibSite(CalibSite):
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
        site_ref_type = 'entomology_by_season'

        if reference_type is not site_ref_type:
            raise Exception("%s does not support %s reference_type, only %s.",
                            self.__class__.__name__, reference_type, site_ref_type)

    def get_analyzers(self):
<<<<<<< HEAD
<<<<<<< HEAD
        return [ChannelBySeasonSpatialCohortAnalyzer(site=self, seasons=self.metadata['months'])]
=======
        return [ChannelBySeasonCohortAnalyzer(site=self, seasons=self.metadata['months'])]
>>>>>>> Small changes to spatial manager files
=======
        return [ChannelBySeasonSpatialCohortAnalyzer(site=self, seasons=self.metadata['months'])]
>>>>>>> Updated spatial analyzer and spatial entomology calib site
