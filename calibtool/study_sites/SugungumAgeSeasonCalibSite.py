import logging
import os
import numpy as np

from calibtool.study_sites.DensityCalibSite import DensityCalibSite

logger = logging.getLogger(__name__)


class SugungumAgeSeasonCalibSite(DensityCalibSite):
    metadata = {
        'parasitemia_bins': [0, 50, 200, 500, np.inf],  # (, 0] (0, 50] ... (50000, ]
        'age_bins': [0, 5, 15, np.inf],  # (, 5] (5, 15] (15, ],
        'seasons': ['DC2', 'DH2', 'W2'],
        'seasons_by_month': {
            'May': 'DH2',
            'September': 'W2',
            'January': 'DC2'
        },
        'village': 'Sugungum'
    }

    reference_csv = os.path.join(os.path.dirname(os.getcwd()), 'calibtool', 'study_sites', 'GarkiDB.csv')

    def __init__(self):
        super(SugungumAgeSeasonCalibSite, self).__init__('Sugungum')
