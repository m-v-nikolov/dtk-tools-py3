import logging
from collections import OrderedDict

from calibtool.study_sites import site_BFdensity
from calibtool.CalibSite import CalibSite
from calibtool.analyzers.PrevalenceByAgeSeasonAnalyzer import PrevalenceByAgeSeasonAnalyzer
from calibtool.analyzers.Helpers import season_channel_age_density_json_to_pandas

logger = logging.getLogger(__name__)


class LayeCalibSite(CalibSite):

    metadata = {
        # TODO: be explicit with categorical bins?
        # http://pandas.pydata.org/pandas-docs/stable/categorical.html
        # (, 0] (0, 50] (50, 500] ...
        # (, 5] (5, 15] (15, 1000]
        # [180, 211] [246, 282] [10, 33]

        "parasitemia_bins": [0, 50, 500, 5000, 50000, 500000],
        "age_bins": [5, 15, 1000],

        # TODO: resolve discrepancy?
        # From Prashanth's branch
        # "months": ['April', 'August', 'December']

        # From Malaria Journal paper (Methods)
        # 1 July, 1 Sept, 1 March

        # From Andre's raw data
        # START_WET = 29 June - 30 July '07 = 180 - 211 (doy)
        # PEAK_WET = 3 Sept - 9 Oct '07 = 246 - 282 (doy)
        # END_WET (DRY) = 10 Jan - 2 Feb '08 = 10 - 33 (doy)
        "months": ['July', 'September', 'January']
    }

    def __init__(self):
        super(LayeCalibSite, self).__init__('Laye')

    def get_reference_data(self, reference_type):

        site_ref_type = 'density_by_age_and_season'

        if reference_type is not site_ref_type:
            raise Exception("%s does not support %s reference_type, only %s.",
                            self.__class__.__name__, reference_type, site_ref_type)

        reference_dict = {
            # Digitized by J.Gerardin from data in:
            #   - A.L.Ouedraogo et al. JID 2015
            # for J.Gerardin et al. Malaria Journal 2015, 14:231
            "start_wet": {
                "PfPR by Parasitemia and Age Bin": [
                    [2, 0, 0, 0, 1, 1], [4, 1, 2, 3, 2, 6], [7, 9, 4, 2, 4, 1]],
                "PfPR by Gametocytemia and Age Bin": [
                    [0, 0, 0, 5, 0, 0], [3, 9, 8, 1, 0, 0], [16, 4, 6, 1, 0, 0]]
            },
            "peak_wet": {
                "PfPR by Parasitemia and Age Bin": [
                    [0, 1, 0, 1, 1, 0], [13, 1, 0, 3, 0, 1], [9, 12, 3, 0, 1, 0]],
                "PfPR by Gametocytemia and Age Bin": [
                    [1, 0, 1, 1, 0, 0], [2, 4, 8, 4, 1, 0], [7, 10, 5, 3, 0, 0]]
            },
            "end_wet": {
                "PfPR by Parasitemia and Age Bin": [
                    [1, 0, 0, 0, 1, 0], [8, 1, 1, 6, 3, 1], [10, 11, 4, 2, 0, 0]],
                "PfPR by Gametocytemia and Age Bin": [
                    [1, 0, 0, 1, 0, 0], [7, 9, 3, 1, 0, 0], [14, 10, 3, 0, 0, 0]]
            }
        }

        reference_bins = OrderedDict([
            ('Age Bins', self.metadata['age_bins']),
            ('PfPR bins', self.metadata['parasitemia_bins'])
        ])

        reference_data = season_channel_age_density_json_to_pandas(reference_dict, reference_bins)

        logger.debug('Reference data:\n  %s', reference_data)
        return reference_data

    def get_setup_function(self):
        return site_BFdensity.get_setup_functions('Laye')

    def get_analyzers(self):

        # TODO: fix this for any customization arguments, e.g. the Metadata currently in the reference_data dictionary

        return [PrevalenceByAgeSeasonAnalyzer(site=self)]
