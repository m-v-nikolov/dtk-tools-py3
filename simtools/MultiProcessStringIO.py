import inspect
import os

from multiprocessing import Lock
from StringIO import StringIO

class PidIndex(object):
    """
    Allows execution of StringIO method calls with a temporary read index, restoring original buffer position
    upon __exit__ . The given pid's read index will be updated to reflect the final read index at __exit__
    """
    def __init__(self, pid, io):
        pid = int(pid)
        self.pid = pid
        self.io = io
        self.original_pos = None

    def __enter__(self):
        # This is in case this object has been closed; this will give us the proper complaint
        if not hasattr(self.io, 'pos'):
            self.io.pos = None

        self.original_pos = self.io.pos
        self.io.pos = self.io._read_positions[self.pid]

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.io._read_positions[self.pid] = self.io.pos # update this pid's read index for next time
        self.io.pos = self.original_pos

class NotRegistered(Exception): pass

class MultiProcessStringIO(StringIO):
    """
    This class allows multiple processes to keep individual buffer read indicies so that reading by one process
    does not affect the read indicies of other processes. To use it, simply have every process that wants to use it
    call .register() on an instance of MultiProcessStringIO . Make sure that .close() is called only after all
    processes that may want to read from the object are done with it (else they'll get a 'is closed' error)
    """

    def __init__(self, buf='', lock=None):
        # super(MemoizedStringIO, self).__init__(buf=buf)
        StringIO.__init__(self, buf=buf)
        self._lock = lock or Lock()
        self._read_positions = {}

    @property
    def _registered_processes(self):
        return self._read_positions.keys()

    def _super_interface(self, method, **kwargs):
        """
        This is the method that calls the specified superclass method. It ensures the given pid's read index is used
        and properly updated.
        :param method: The superclass method to call
        :param kwargs: args for the superclass method
        :return: whatever the specified method returns
        """
        if not 'pid' in kwargs:
            kwargs['pid'] = os.getpid()
        pid = int(kwargs.pop('pid'))
        with self._lock:
            if pid not in self._registered_processes:
                raise NotRegistered('Current process is not registered to use this MultiProcessStringIO object.')
            with PidIndex(pid=pid, io=self):
                return StringIO.read(self, **kwargs)

    def register(self, pid=os.getpid()):
        """
        Create a read index for the specified (or current) process. Will not alter the read index if pid is already
        registered.
        :return: the pid of the registered process
        """
        pid = int(pid)
        with self._lock:
            if pid not in self._registered_processes:
                self._read_positions[pid] = 0 # create a new read index at the beginning
        return pid

    def unregister(self, pid=os.getpid()):
        """
        Remove this process's read index.
        :param pid: a process id (int)
        :return: the pid that was unregistered, None if pid was not registered
        """
        pid = int(pid)
        with self._lock:
            if self._read_positions.pop(pid, None) is not None:
                return pid
            else:
                return None

    # These are the StringIO methods that are extended for multi-process use
    def read(self, **kwargs):
        method = inspect.stack()[0][3]
        return self._super_interface(method, **kwargs)

    def readline(self, **kwargs):
        method = inspect.stack()[0][3]
        return self._super_interface(method, **kwargs)

    def readlines(self, **kwargs):
        method = inspect.stack()[0][3]
        return self._super_interface(method, **kwargs)

    def seek(self, **kwargs):
        method = inspect.stack()[0][3]
        return self._super_interface(method, **kwargs)

