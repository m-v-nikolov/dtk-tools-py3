import logging

from calibtool.study_sites.PrevalenceCalibSite import PrevalenceCalibSite

logger = logging.getLogger(__name__)


class NamawalaCalibSite(PrevalenceCalibSite):

    reference_dict = {

        # Digitized by K.McCarthy from data in:
        #   - TODO: Namawala original source reference and/or 2006 Swiss TPH supplement?
        # for K.McCarthy et al. Malaria Journal 2015, 14:6

        "Average Population by Age Bin": [
            150, 150, 626, 1252, 626, 2142,
            1074, 1074, 605, 605, 489
        ],
        "Age Bin": [
            0.5, 1, 2, 4, 5, 10,
            15, 20, 30, 40, 50
        ],
        "PfPR by Age Bin": [
            0.55, 0.85, 0.9, 0.88, 0.85, 0.82,
            0.75, 0.65, 0.45, 0.42, 0.4
        ]
    }

    def __init__(self):
        super(NamawalaCalibSite, self).__init__('Namawala')
