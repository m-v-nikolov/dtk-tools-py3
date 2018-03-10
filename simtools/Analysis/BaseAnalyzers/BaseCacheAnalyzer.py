from simtools.Analysis.BaseAnalyzers.BaseAnalyzer import BaseAnalyzer

class BaseCacheAnalyzer(BaseAnalyzer):

    def __init__(self, cache_location=None, force=False):
        super().__init__()
        self.cache_location = cache_location
        self.cache = None
        self.force = force

    def initialize(self):
        from diskcache import Cache
        self.cache = Cache(self.cache_location or self.uid + "_cache")

    def filter(self, simulation):
        return self.force or not self.is_in_cache(simulation.id)

    def to_cache(self, key, data):
        self.cache.set(key, data)

    def from_cache(self, key):
        return self.cache.get(key)

    def is_in_cache(self, key):
        return key in self.cache

    def __del__(self):
        if self.cache:
            self.cache.close()

    @property
    def keys(self):
        return list(self.cache.iterkeys()) if self.cache else None
