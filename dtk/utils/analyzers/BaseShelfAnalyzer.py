import shelve

from multiprocessing import Lock

from dtk.utils.analyzers.BaseAnalyzer import BaseAnalyzer


class BaseShelfAnalyzer(BaseAnalyzer):

    def __init__(self, shelf_filename=None, lock=None):
        super(BaseShelfAnalyzer, self).__init__()
        self.shelf_filename = shelf_filename or self.__class__.__name__ + ".shelf"
        self._shelf = None # must set in initialize()
        self._lock = lock or Lock()
        self.multiprocessing_plot = False

    def initialize(self):
        # create the shelf to use
        self._shelf = shelve.open(self.shelf_filename, writeback=True)

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
        value = True
        try:
            self._shelf[str(key)]
        except KeyError:
            value = False
        return value

    def __del__(self):
        self._shelf.close()
