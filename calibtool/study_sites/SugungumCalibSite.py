import logging

from calibtool.study_sites.PrevalenceCalibSite import PrevalenceCalibSite

logger = logging.getLogger(__name__)


class SugungumCalibSite(PrevalenceCalibSite):

    reference_dict = {

        # Digitized by K.McCarthy from data in:
        #   - TODO: Garki Project reference and/or 2006 Swiss TPH supplement?
        # for K.McCarthy et al. Malaria Journal 2015, 14:6

        "Average Population by Age Bin": [
            79, 79, 114, 229, 114, 669,
            314, 324, 733, 829, 582, 418
        ],
        "Age Bin": [
            0.5, 1, 2, 4, 5, 10,
            15, 20, 30, 40, 50, 60
        ],
        "PfPR by Age Bin": [
            0.3, 0.68, 0.75, 0.82, 0.88, 0.76,
            0.6, 0.42, 0.27, 0.22, 0.25, 0.32
        ]
    }

    def __init__(self):
        super(SugungumCalibSite, self).__init__('Sugungum')
