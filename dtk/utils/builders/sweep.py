import itertools
from collections import deque

from dtk.vector.study_sites import configure_site
from dtk.vector.calibration_sites import set_calibration_site

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

def param_fn(k,v):
    def fn(cb):
        Builder.metadata.update({k:v})
        cb.set_param(k,v)
    return fn

def site_fn(s, calib=False):
    def fn(cb):
        Builder.metadata.update({'_site_':s})
        if calib:
            set_calibration_site(cb,s)
        else:
            configure_site(cb,s)
    return fn

def custom_fn(desc,mod_fn,*args,**kwargs):
    def fn(cb):
        Builder.metadata.update({desc:kwargs})
        mod_fn(cb,*args,**kwargs)
    return fn

def set_mods(pv_pairs):
    m=Builder.ModList()
    pv_dict=dict(pv_pairs)

    # Site setup first: configure_site() shouldn't override other parameters
    site=pv_dict.pop('_site_',None)
    calibsite=pv_dict.pop('_calibsite_',None)
    if calibsite and site: 
        raise Exception('Trying to sweep over sites in two incompatible ways.')
    elif site:
        m.append(site_fn(site))
    elif calibsite:
        m.append(site_fn(calibsite,calib=True))

    for (p,v) in pv_dict.items():
        if p and p[0]=='_': # call specified function + args
            args=deque(v)
            mod_fn=args.popleft()
            kwargs=args.pop()
            m.append(custom_fn(p,mod_fn,*args,**kwargs))
        else:
            m.append(param_fn(p,v))
    return m

class SingleSimulationBuilder(Builder):
    def __init__(self):
        self.mod_generator = (Builder.ModList() for _ in range(1))

class RunNumberSweepBuilder(Builder):
    def __init__(self,nsims):
        self.mod_generator = (set_mods([('Run_Number',i)]) for i in range(nsims))

class GenericSweepBuilder(Builder):
    @classmethod
    def from_dict(cls, d):
        params=d.keys()
        combos=itertools.product(*d.values())
        return cls((set_mods(zip(params,combo)) for combo in combos))

    @classmethod
    def from_list(cls, p, v) :
        return cls((set_mods(zip(p,combo)) for combo in v))