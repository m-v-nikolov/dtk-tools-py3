import itertools

from SimConfigBuilder import SimConfigBuilder


class ModList(list):
    def __init__(self, *args):
        ModBuilder.metadata = {}
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

        # Make sure we cast numpy types into normal system types
        for k, v in md.iteritems():
            import numpy as np
            if isinstance(v, (np.int64, np.float64, np.float32, np.uint32, np.int16, np.int32)):
                md[k] = v.item()

        # Store the metadata in a class variable
        ModBuilder.metadata.update(md)
        # But also return the metadata because of muddleheaded use
        # TODO: Unify the way we handle metadata by removing the storage in the ModBuilder.metadata
        return md


class ModBuilder(object):
    """
    Classes derived from ModBuilder have generators that
    yield ModList(ModFn(cb), ModFn(cb), ...)
    where each ModFn modifies the base SimConfigBuilder (cb)
    and builds a ModBuilder.metadata dict that is reset on ModList init
    """
    metadata = {}

    def __init__(self, mod_generator):
        self.tags = {}
        self.mod_generator = mod_generator

    @classmethod
    def set_mods(cls, funcs):
        """
        Construct the list of ModFns to be applied to each simulation,
        verifying that only one site-configuration call is made and that it is done first.
        """
        funcs = list(funcs)  # to allow reordering

        site_mods = [s for s in funcs if s.fname in ('configure_site', 'set_calibration_site')]

        if len(site_mods) > 1:
            raise ValueError('Only supporting a maximum of one call to configure_site or set_calibration_site.')

        if site_mods:
            funcs.insert(0, funcs.pop(funcs.index(site_mods[0])))  # site configuration first

        m = ModList()
        for func in funcs:
            m.append(func)

        return m

    @classmethod
    def from_combos(cls, *modlists):
        combos = itertools.product(*modlists)
        return cls.from_list(combos)

    @classmethod
    def from_list(cls, combos):
        return cls((cls.set_mods(combo) for combo in combos))


class SingleSimulationBuilder(ModBuilder):
    def __init__(self):
        self.tags = {}
        self.mod_generator = (ModList() for _ in range(1))


class RunNumberSweepBuilder(ModBuilder):
    def __init__(self, nsims):
        self.tags = {}
        self.mod_generator = (ModList(ModFn(SimConfigBuilder.set_param, 'Run_Number', i)) for i in range(nsims))
