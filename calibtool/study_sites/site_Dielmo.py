import logging

from calibtool.study_sites import site_clinical_incidence_cohort
from calibtool.CalibSite import CalibSite
from calibtool.analyzers.ClinicalIncidenceByAgeCohortAnalyzer import ClinicalIncidenceByAgeCohortAnalyzer

logger = logging.getLogger(__name__)


class DielmoCalibSite(CalibSite):

    def __init__(self):
        super(DielmoCalibSite, self).__init__('Dielmo')

    def get_reference_data(self, reference_type):

        site_ref_type = 'annual_clinical_incidence_by_age'

        if reference_type is not site_ref_type:
            raise Exception("%s does not support %s reference_type, only %s.",
                            self.__class__.__name__, reference_type, site_ref_type)

        reference_data = {
            "n_obs": [
                55, 60, 55, 50, 50,
                38, 38, 38, 38, 38,
                26, 26, 26, 26, 26,
                110, 75, 75, 150, 70, 70, 90],
            "age_bins": [
                1, 2, 3, 4, 5,
                6, 7, 8, 9, 10,
                11, 12, 13, 14, 15,
                20, 25, 30, 40, 50, 60, 100],
            "Annual Clinical Incidence by Age Bin": [
                3.2, 5, 6.1, 4.75, 3.1,
                2.75, 2.7, 1.9, 0.12, 0.8,
                0.5, 0.25, 0.1, 0.2, 0.4,
                0.3, 0.2, 0.2, 0.2, 0.15, 0.15, 0.15]
        }

        logger.debug('Reference data:\n  %s', reference_data)
        return reference_data

    def get_setup_function(self):
        return site_clinical_incidence_cohort.get_setup_functions('Dielmo')

    def get_analyzers(self):
        return [ClinicalIncidenceByAgeCohortAnalyzer(site=self)]
