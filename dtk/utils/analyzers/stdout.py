import logging

from dtk.utils.analyzers.BaseAnalyzer import BaseAnalyzer

logger = logging.getLogger(__name__)


class StdoutAnalyzer(BaseAnalyzer):
    def __init__(self, simIds=None, error=False):
        self.filenames = ['StdOut.txt', 'StdErr.txt']
        self.simIds = simIds
        self.error = error

    def filter(self, sim_metadata):
        return lambda x: True

    def apply(self, parser):
        if self.error:
            parser.stdout = parser.raw_data[self.filenames[1]]
        else:
            parser.stdout = parser.raw_data[self.filenames[0]]

    def combine(self, parsers):
        if self.simIds is not None:
            try:
                selected = [parsers.get(k).stdout for k in self.simIds]
            except:
                logger.error('Bad simulation id(s).')
                raise Exception('Bad simulation id(s).')
        else:
            selected = [parsers.get(k).stdout for k in parsers][:1]

        combined = ''.join(selected)
        self.data = combined

    def finalize(self):
        print self.data
