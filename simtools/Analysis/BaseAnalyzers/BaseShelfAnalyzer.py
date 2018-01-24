import shelve

from multiprocessing import Lock

import os

from simtools.Analysis.BaseAnalyzers.BaseAnalyzer import BaseAnalyzer


class BaseShelfAnalyzer(BaseAnalyzer):

    def __init__(self, shelf_filename=None, lock=None, shelf_location=None):
        super(BaseShelfAnalyzer, self).__init__()
        self.shelf_filename = shelf_filename or self.__class__.__name__ + ".shelf"
        self._shelf = None # must set in initialize()
        self._lock = lock or Lock()
        self.shelf_location = shelf_location

    def initialize(self):
        # Make sure the subdirectory exist
        if self.shelf_location:
            if not os.path.exists(self.shelf_location):
                os.makedirs(self.shelf_location)
        # create the shelf to use
        self._shelf = shelve.open(os.path.join(self.shelf_location or "", self.shelf_filename), writeback=True)

    def shelf_keys(self):
        return list(self._shelf.keys())

    def update_shelf(self, key, value):
        with self._lock:
            self._shelf[str(key)] = value
            self._shelf.sync()

    def from_shelf(self, key):
        key = str(key)
        try:
            value = self._shelf[key]
        except KeyError:
            value = None
        return value

    def is_in_shelf(self, key):
        return key in self._shelf

    def __del__(self):
        self._shelf.close()
