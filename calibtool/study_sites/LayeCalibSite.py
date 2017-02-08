import logging
from collections import OrderedDict

import numpy as np
from calibtool.analyzers.Helpers import season_channel_age_density_json_to_pandas

from calibtool.study_sites.DensityCalibSite import DensityCalibSite

logger = logging.getLogger(__name__)


class LayeCalibSite(DensityCalibSite):

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
                [2, 0, 0, 0, 1, 1],
                [4, 1, 2, 3, 2, 6],
                [7, 9, 4, 2, 4, 1]
            ],
            "PfPR by Gametocytemia and Age Bin": [
                [0, 0, 0, 5, 0, 0],
                [3, 9, 8, 1, 0, 0],
                [16, 4, 6, 1, 0, 0]
            ]
        },
        "peak_wet": {
            "PfPR by Parasitemia and Age Bin": [
                [0, 1, 0, 1, 1, 0],
                [13, 1, 0, 3, 0, 1],
                [9, 12, 3, 0, 1, 0]
            ],
            "PfPR by Gametocytemia and Age Bin": [
                [1, 0, 1, 1, 0, 0],
                [2, 4, 8, 4, 1, 0],
                [7, 10, 5, 3, 0, 0]
            ]
        },
        "end_wet": {
            "PfPR by Parasitemia and Age Bin": [
                [1, 0, 0, 0, 1, 0],
                [8, 1, 1, 6, 3, 1],
                [10, 11, 4, 2, 0, 0]
            ],
            "PfPR by Gametocytemia and Age Bin": [
                [1, 0, 0, 1, 0, 0],
                [7, 9, 3, 1, 0, 0],
                [14, 10, 3, 0, 0, 0]
            ]
        }
    }

    def get_reference_data(self, reference_type):
        super(LayeCalibSite, self).get_reference_data(reference_type)

        reference_bins = OrderedDict([
            ('Age Bin', self.metadata['age_bins']),
            ('PfPR Bin', self.metadata['parasitemia_bins'])
        ])
        reference_data = season_channel_age_density_json_to_pandas(self.reference_dict, reference_bins)

        return reference_data

    def __init__(self):
        super(LayeCalibSite, self).__init__('Laye')

