from tempfile import mkdtemp

import shutil
from diskcache import FanoutCache, Cache, Deque


class CacheEnabled:

    def __init__(self):
        self.cache_directory = None
        self.cache = None
        self.queue = False

    def initialize_cache(self, shards=None, timeout=1, queue=False):
        self.reset_cache()

        # Create a temporary directory for the cache
        self.cache_directory = mkdtemp()

        # Create a queue?
        if queue:
            self.cache = Deque(directory=self.cache_directory)
            self.queue = True
        elif shards:
            self.cache = FanoutCache(self.cache_directory, shards=shards, timeout=timeout)
            self.queue = False
        else:
            self.cache = Cache(self.cache_directory, timeout=timeout)
            self.queue = False

        return self.cache

    def reset_cache(self):
        # If already initialized, destroy and recreate
        if self.cache and not self.queue:
            self.cache.close()
        else:
            del self.cache

        if self.cache_directory:
            shutil.rmtree(self.cache_directory)

    def __del__(self):
        self.reset_cache()

