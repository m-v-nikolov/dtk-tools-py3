import json

from simtools.Analysis.BaseAnalyzers import BaseAnalyzer
from simtools.Utilities.Encoding import GeneralEncoder


class BaseCalibrationAnalyzer(BaseAnalyzer):
    def __init__(self, uid=None, working_dir=None, parse=True, need_dir_map=False, filenames=None,
                 reference_data=None, weight=1):
        super().__init__(uid, working_dir, parse, need_dir_map, filenames)
        self.reference_data = reference_data
        self.weight = weight

    def cache(self):
        return json.dumps(self, cls=GeneralEncoder)

    # For retro compatibility
    # Will disappear with the calibtool 2.0
    @property
    def name(self):
        return self.uid

    @property
    def result(self):
        return self.results

    @result.setter
    def result(self, value):
        self.results = value

    # End retro compatibility
