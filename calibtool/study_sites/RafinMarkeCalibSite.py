import logging

from calibtool.study_sites.PrevalenceCalibSite import PrevalenceCalibSite

logger = logging.getLogger(__name__)


class RafinMarkeCalibSite(PrevalenceCalibSite):

    reference_dict = {

        # Digitized by K.McCarthy from data in:
        #   - TODO: Garki Project reference and/or 2006 Swiss TPH supplement?
        # for K.McCarthy et al. Malaria Journal 2015, 14:6

        "Average Population by Age Bin": [
            45, 45, 66, 132, 66, 386,
            182, 187, 424, 479, 336, 241
        ],
        "Age Bin": [
            0.5, 1, 2, 4, 5, 10,
            15, 20, 30, 40, 50, 60
        ],
        "PfPR by Age Bin": [
            0.44, 0.5, 0.55, 0.8, 0.85, 0.83,
            0.68, 0.55, 0.35, 0.25, 0.2, 0.15
        ]
    }

    def __init__(self):
        super(RafinMarkeCalibSite, self).__init__('Rafin_Marke')
