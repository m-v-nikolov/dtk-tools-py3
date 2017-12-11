from dtk.utils.analyzers.BaseAnalyzer import BaseAnalyzer

from threading import Lock
import shelve, os

class BaseShelveAnalyzer(BaseAnalyzer):
    """
    A class that provides caching support via shelve to analyzers.
    """

    # Shelve files are not thread safe, need a common mutex
    mutex = Lock()


    def __init__(self, force_apply, force_combine, verbose):
        """
        Call this function from your analyzer's __init__ to initialize shelving

        :param force_apply: Set True to override all previous caching.  Implies force_combine
        :param force_combine: Set True to recompute the combine() analysis step instead of retrieving results from the shelve-based cache
        :param verbose: Verbose if True
        """
        super(BaseShelveAnalyzer, self).__init__()
        self.force_apply = force_apply
        self.force_combine = force_combine
        self.verbose = verbose
        self.multiprocessing_plot = False

        if self.force_apply and not self.force_combine:
            if self.verbose:
                print("force_apply is True, but force_combine is False.  Setting force_combine = True to avoid using a stale shelve cache.")
            self.force_combine = True

        self.shelve = None

        self.shelve_file = None


    def shelve_apply(self, sim_id, data):
        """
        Call shelve_apply to store the results of your apply() function for a particular sim_id.
        :param sim_id: the id of simulation on which apply is being called
        :param data: the data you would like to shelve for this simulation
        """

        self.shelve_write(str(sim_id), data)


    def shelve_combine(self, data):
        """
        Call shelve_combine to store the results of your combine() function.
        :param data: the data you would like to shelve
        """

        self.shelve_write('combine', data)


    def filter(self, shelve_file, sim_metadata):
        """
        Call filter on simulations you would like to analyze or retrieve from shelve

        :param shelve_file: the path to the shelve file, typically a *.db file.
        :param sim_metadata: the metadata passed to the filter function.
        """

        ## LOCK FOR SHELVE ####################################################
        self.mutex.acquire()

        if self.shelve is None:
            self.shelve_file = shelve_file
            if self.verbose:
                print ("Opening shelve file: %s" % self.shelve_file)

            self.shelve = shelve.open(self.shelve_file)

            if self.force_apply:
                if self.verbose:
                    print ("User set force_apply = True, so clearing the shelve.")
                self.shelve.clear()

        if 'status' in self.shelve:
            pass
            if self.shelve['status'] in ['combine', 'finalize'] and not self.force_combine:   # past apply, don't need to download any files
                if self.verbose:
                    print ('shelve status is %s, so returning False from filter' % self.shelve['status'])
                self.mutex.release()
                return False
        else:
            if self.verbose:
                print ("Setting shelve status to filter")
            self.shelve['status'] = 'filter' # Already have lock, don't call shelve_write

        sim_id = sim_metadata['sim_id']
        if str(sim_id) not in self.shelve:
            self.mutex.release()
            return True

        self.mutex.release()
        return False
        #######################################################################


    def apply(self, parser):
        """
        Call this base apply from your analyzer's apply.
        It will simply note in the shelve that the current analysis step is 'apply'
        """

        self.shelve_write('status', 'apply')


    def combine(self, parsers):
        """
        Call this base combine from your analyzer's combine.
        It will note in the shelve that the current analysis step is 'combine' and return previously shelved results of combine.
        :param parsers: baes method from dtk-tools
        :returns: Previously cached combine results, if any, and None otherwise.
        """

        self.shelve_write('status', 'combine')

        if 'combine' in self.shelve and not self.force_combine:
            return self.shelve['combine']

        return None


    def finalize(self):
        """
        Call this base finalize from your analyzer's finalize.
        Updates status to finalize and closes the shelve.
        """

        self.shelve_write('status', 'finalize')
        self.shelve.close()
        self.shelve = None
        self.shelve_file = None


    def shelve_write(self, key, value):
        """
        Helper function to get a lock before modifying the shelve.  Also syncs.
        :param key: the key where the data should be stored
        :param data: the data to store at key
        """
        self.mutex.acquire()
        self.shelve[key] = value
        self.shelve.sync()
        self.mutex.release()


