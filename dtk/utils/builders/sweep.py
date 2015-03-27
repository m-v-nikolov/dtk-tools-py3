import itertools
from dtk.vector.study_sites import configure_site

class Builder(object):
    '''
    Classes derived from Builder have generators that
    yield ModList(fn1(cb),fn2(cb),...) 
    where each function (fn) modifies the base ConfigBuilder (cb)
    and builds up metadata that is reset on ModList init
    '''
    metadata={}

    class ModList(list):
        def __init__(self, *args):
            Builder.metadata={}
            list.__init__(self, args)

    def __init__(self, mod_generator):
        self.mod_generator=mod_generator

    @classmethod
    def param_fn(cls,k,v):
        def fn(cb):
            cls.metadata.update({k:v})
            return cb.set_param(k,v)
        return fn

    @classmethod
    def site_fn(cls,s):
        def fn(cb):
            cls.metadata.update({'_site_':s})
            return configure_site(cb,s)
        return fn

    @classmethod
    def set(cls,pv_pairs):
        m=cls.ModList()
        for (p,v) in pv_pairs:
            if p=='_site_':
                m.append(cls.site_fn(v))
            elif p and p[0]=='_':
                raise NotImplementedError('Future general function, e.g. add_event')
            else:
                m.append(cls.param_fn(p,v))
        return m

class DefaultSweepBuilder(Builder):
    def __init__(self):
        self.mod_generator = (self.set([]) for _ in range(1))

class RunNumberSweepBuilder(Builder):
    def __init__(self,nsims):
        self.mod_generator = (self.set([('Run_Number',i)]) for i in range(nsims))

class GenericSweepBuilder(Builder):
    @classmethod
    def from_dict(cls, d):
        params=d.keys()
        combos=itertools.product(*d.values())
        return cls((cls.set(zip(params,combo)) for combo in combos))