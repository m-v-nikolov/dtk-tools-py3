import itertools
from collections import deque

from dtk.vector.study_sites import configure_site
from dtk.vector.calibration_sites import set_calibration_site
from dtk.utils.core.DTKConfigBuilder import set_param

class Builder(object):
    '''
    Classes derived from Builder have generators that
    yield ModList(ModFn(cb),ModFn(cb),...) 
    where each ModFn modifies the base DTKConfigBuilder (cb)
    and builds a Builder.metadata dict that is reset on ModList init
    '''
    metadata={}

    class ModList(list):
        def __init__(self, *args):
            Builder.metadata = {}
            list.__init__(self, args)

    class ModFn(object):
        def __init__(self, func, *args, **kwargs):
            self.func = func
            self.fname = self.func.__name__
            self.args = args
            self.kwargs = kwargs

        def __call__(self, cb):
            md = self.func(cb, *self.args, **self.kwargs)
            if not md:
                md = {'.'.join([self.fname, k]): v for (k, v) in self.kwargs.items()}
            Builder.metadata.update(md)

    def __init__(self, mod_generator):
        self.mod_generator = mod_generator

    @classmethod
    def set_mods(cls, funcs):
        funcs = list(funcs)  # to allow reordering
        m = cls.ModList()
        site_mods = [s for s in funcs if s.fname in ('configure_site', 'set_calibration_site')]
        if len(site_mods) > 1:
            raise ValueError('Only supporting a maximum of one call to configure_site or set_calibration_site.')
        if site_mods:
            funcs.insert(0, funcs.pop(funcs.index(site_mods[0]))) # site configuration first
        for func in funcs:
            m.append(func)
        return m

    @classmethod
    def from_combos(cls, *modlists):
        combos = itertools.product(*modlists)
        return cls.from_list(combos)

    @classmethod
    def from_list(cls, combos) :
        return cls((cls.set_mods(combo) for combo in combos))

class SingleSimulationBuilder(Builder):
    def __init__(self):
        self.mod_generator = (self.ModList() for _ in range(1))

class RunNumberSweepBuilder(Builder):
    def __init__(self, nsims):
        self.mod_generator = (self.set_mods([self.ModFn(set_param, 'Run_Number', i)]) for i in range(nsims))

class GenericSweepBuilder(Builder):
    @classmethod
    def from_dict(cls, d):
        params = d.keys()
        combos = itertools.product(*d.values())
        return cls((cls.set_mods(zip(params, combo)) for combo in combos))

    @classmethod
    def set_mods(cls, pv_pairs):
        def convert_to_mod_fn(pv_pair):
            p, v = pv_pair
            if p == '_site_':
                return Builder.ModFn(configure_site, v)
            if p == '_calibsite_': 
                return Builder.ModFn(set_calibration_site, v)
            return Builder.ModFn(set_param, p, v)

        return Builder.set_mods([convert_to_mod_fn(pv_pair) for pv_pair in pv_pairs])