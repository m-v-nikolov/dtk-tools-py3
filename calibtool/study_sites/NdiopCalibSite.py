import logging

from calibtool.study_sites.IncidenceCalibSite import IncidenceCalibSite

logger = logging.getLogger(__name__)


class NdiopCalibSite(IncidenceCalibSite):

    reference_dict = {

        # Digitized by K.McCarthy from data in:
        #   - Rogier et al. Parassitologia 1999
        #   - Trape et al. Am J Trop Med Hyg 1994
        #   - Rogier and Trape, Med Trop (Marseille) 1995
        # for K.McCarthy et al. Malaria Journal 2015, 14:6

        "Average Population by Age Bin": [
            31, 34, 31, 28, 28,
            21, 21, 21, 21, 21,
            15, 15, 15, 15, 15,
            62, 42, 42, 84, 39, 39, 50],
        "Age Bin": [
            1, 2, 3, 4, 5,
            6, 7, 8, 9, 10,
            11, 12, 13, 14, 15,
            20, 25, 30, 40, 50, 60, 100],
        "Annual Clinical Incidence by Age Bin": [
            1.9, 2.2, 2.6, 2.8, 2.9,
            3.0, 2.8, 2.7, 2.6, 2.6,
            2.5, 2.2, 2.1, 1.8, 1.5,
            1.0, 0.8, 0.6, 0.5, 0.4, 0.3, 0.4]
    }

    def __init__(self):
        super(NdiopCalibSite, self).__init__('Ndiop')
