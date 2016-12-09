import logging

import numpy as np

from calibtool.study_sites.DensityCalibSite import DensityCalibSite

logger = logging.getLogger(__name__)


class DapelogoCalibSite(DensityCalibSite):

    metadata = {
        'parasitemia_bins': [0, 50, 500, 5000, 50000, np.inf],  # (, 0] (0, 50] ... (50000, ]
        'age_bins': [5, 15, np.inf],  # (, 5] (5, 15] (15, ]

        'seasons_by_month': {  # Collection dates from raw data in Ouedraogo et al. JID 2015
            'July': 'start_wet',  # 29 June - 30 July '07 => [180 - 211]
            'September': 'peak_wet',  # 3 Sept - 9 Oct '07 => [246 - 282]
            'January': 'end_wet'  # (a.k.a. DRY) 10 Jan - 2 Feb '08 => [10 - 33]
        }
    }

    reference_dict = {

        # Digitized by J.Gerardin from data in:
        #   - A.L.Ouedraogo et al. JID 2015
        # for J.Gerardin et al. Malaria Journal 2015, 14:231
        # N.B. the values represent counts of individual observations

        "start_wet": {
            "PfPR by Parasitemia and Age Bin": [
                [1, 0, 0, 2, 2, 3],
                [2, 1, 0, 2, 0, 4],
                [9, 5, 4, 4, 2, 3]
            ],
            "PfPR by Gametocytemia and Age Bin": [
                [0, 1, 4, 2, 2, 0],
                [0, 1, 4, 6, 0, 0],
                [12, 8, 3, 4, 0, 0]
            ]
        },
        "peak_wet": {
            "PfPR by Parasitemia and Age Bin": [
                [1, 2, 0, 1, 3, 1],
                [2, 5, 2, 3, 1, 1],
                [6, 8, 4, 4, 0, 2]
            ],
            "PfPR by Gametocytemia and Age Bin": [
                [1, 3, 2, 2, 0, 0],
                [0, 8, 0, 3, 0, 0],
                [11, 10, 2, 2, 0, 0]
            ]
        },
        "end_wet": {
            "PfPR by Parasitemia and Age Bin": [
                [1, 1, 0, 4, 3, 1],
                [4, 1, 2, 4, 2, 1],
                [6, 9, 6, 2, 2, 0]
            ],
            "PfPR by Gametocytemia and Age Bin": [
                [2, 3, 2, 2, 1, 0],
                [2, 5, 4, 2, 1, 0],
                [14, 7, 4, 0, 0, 0]
            ]
        }
    }

    def __init__(self):
        super(DapelogoCalibSite, self).__init__('Dapelogo')

