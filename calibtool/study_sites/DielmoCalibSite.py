import logging

from calibtool.study_sites.IncidenceCalibSite import IncidenceCalibSite

logger = logging.getLogger(__name__)


class DielmoCalibSite(IncidenceCalibSite):

    reference_dict = {

        # Digitized by K.McCarthy from data in:
        #   - Rogier et al. Parassitologia 1999
        #   - Trape et al. Am J Trop Med Hyg 1994
        #   - Rogier and Trape, Med Trop (Marseille) 1995
        # for K.McCarthy et al. Malaria Journal 2015, 14:6

        "Average Population by Age Bin": [
            55, 60, 55, 50, 50,
            38, 38, 38, 38, 38,
            26, 26, 26, 26, 26,
            110, 75, 75, 150, 70, 70, 90],
        "Age Bin": [
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

    def __init__(self):
        super(DielmoCalibSite, self).__init__('Dielmo')
