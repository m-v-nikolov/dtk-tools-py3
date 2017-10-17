import logging

from dtk.utils.analyzers.BaseAnalyzer import BaseAnalyzer

logger = logging.getLogger(__name__)


class StdoutAnalyzer(BaseAnalyzer):
    def __init__(self, simIds=None, error=False):
        super(StdoutAnalyzer, self).__init__()
        self.filenames = ['StdOut.txt', 'StdErr.txt' ]
        self.simIds = simIds
        self.error = error

    def filter(self, sim_metadata):
        return sim_metadata['sim_id'] in self.simIds

    def apply(self, parser):
        try:
            if self.error:
                parser.stdout = parser.raw_data[self.filenames[1]]
            else:
                parser.stdout = parser.raw_data[self.filenames[0]]
        except:
            pass # errors are produced upstream.

    def combine(self, parsers):
        selected = []
        try:
            if self.simIds is not None:
                selected = [parsers.get(k).stdout for k in self.simIds]
            else:
                selected = [parsers.get(k).stdout for k in parsers][:1]
        except:
            pass # errors are produced upstream.

        combined = ''.join(selected)
        self.data = combined

    def finalize(self):
        print(self.data)
