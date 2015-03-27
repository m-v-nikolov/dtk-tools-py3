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

    def param_fn(self,k,v):
        def fn(cb):
            Builder.metadata.update({k:v})
            return cb.set_param(k,v)
        return fn

    def site_fn(self,s):
        def fn(cb):
            Builder.metadata.update({'_site_':s})
            return configure_site(cb,s)
        return fn

class DefaultSweepBuilder(Builder):
    def __init__(self):
        self.mod_generator = (self.ModList(lambda cb:None) for _ in range(1))

class RunNumberSweepBuilder(Builder):
    def __init__(self,nsims):
        self.mod_generator = (self.ModList(self.param_fn('Run_Number',i)) \
                              for i in range(nsims))