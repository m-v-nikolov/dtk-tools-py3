import logging

from calibtool.study_sites.PrevalenceCalibSite import PrevalenceCalibSite

logger = logging.getLogger(__name__)


class MatsariCalibSite(PrevalenceCalibSite):

    reference_dict = {

        # Digitized by K.McCarthy from data in:
        #   - TODO: Garki Project reference and/or 2006 Swiss TPH supplement?
        # for K.McCarthy et al. Malaria Journal 2015, 14:6

        "Average Population by Age Bin": [
            52, 52, 76, 151, 76, 441,
            207, 214, 484, 547, 384, 276
        ],
        "Age Bin": [
            0.5, 1, 2, 4, 5, 10,
            15, 20, 30, 40, 50, 60
        ],
        "PfPR by Age Bin": [
            0.2, 0.68, 0.7, 0.85, 0.8, 0.8,
            0.78, 0.55, 0.35, 0.3, 0.25, 0.3
        ]
    }

    def __init__(self):
        super(MatsariCalibSite, self).__init__('Matsari')