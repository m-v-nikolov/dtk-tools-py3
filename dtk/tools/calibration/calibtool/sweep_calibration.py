from dtk.utils.builders.sweep import Builder
from dtk.tools.calibration.calibtool.geography_calibration import set_geography as set_geography_calibration

class CalibBuilder(Builder):

    def __init__(self, mod_generator):
        self.mod_generator=mod_generator

    @classmethod
    def calib_site_fn(cls,s, geographies):
        def fn(cb):
            cls.metadata.update({'_site_':s})
            return set_geography_calibration(cb, s, geographies)
        return fn

    @classmethod
    def set_calib(cls,pv_pairs, geographies):
        m=cls.ModList()
        if '_site_' in dict(pv_pairs) : # do site first so that configure_sites won't overwrite other sweep parameters
            m.append(cls.calib_site_fn(dict(pv_pairs)['_site_'], geographies))
        for (p,v) in pv_pairs:
            if p=='_site_' :
                continue
            elif p.split('_')[0] == 'AntiMalDrug' : # to sweep over a drug parameter, use 'Drug_DRUGNAME_PARAMNAME' as parameter name in script file
                drugname = p.split('_')[1]
                drugp = '_'.join(p.split('_')[2:])
                m.append(cls.drug_param_changes_fn(drugname,drugp,v)) 
            elif p.split('_')[0] == 'VectorSpec' : # to sweep over a vector species parameter, use 'Vector_VECTORNAME_PARAMNAME' as parameter name in script file
                vector = p.split('_')[1]
                vecp = '_'.join(p.split('_')[2:])
                m.append(cls.vector_species_param_changes_fn(vector,vecp,v))
            elif p and p[0]=='_':
                raise NotImplementedError('Future general function, e.g. add_event')
            else:
                m.append(cls.param_fn(p,v))
        return m

class GenericSweepBuilder(CalibBuilder):

    @classmethod
    def from_list(cls, p, v, geographies) :
        return cls((cls.set_calib(zip(p,combo), geographies) for combo in v))
