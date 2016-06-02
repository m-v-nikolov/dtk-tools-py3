import itertools

from calibtool.study_sites.set_calibration_site import set_calibration_site
from simtools.ModBuilder import ModBuilder

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.vector.study_sites import configure_site


class RunNumberSweepBuilder(ModBuilder):
    def __init__(self, nsims):
        self.mod_generator = (
            self.set_mods(
                [self.ModFn(DTKConfigBuilder.set_param, 'Run_Number', i)]
            ) for i in range(nsims)
        )


class GenericSweepBuilder(ModBuilder):
    '''
    A convenient syntax for simple sweeps over configuration parameters.
    '''

    @classmethod
    def from_dict(cls, d):
        '''
        Generates lists of functions to override parameters for each combination of values.

        :param d: a dictionary of parameter names to lists of parameter values to sweep over.
        '''
        params = d.keys()
        combos = itertools.product(*d.values())
        return cls((cls.set_mods(zip(params, combo)) for combo in combos))

    @classmethod
    def set_mods(cls, pv_pairs):
        '''
        Dictionary may include the special keys: '__site__' or '__calibsite___',
        which are recognized as shorthand for site-configuration functions
        with the site name as the "parameter value".
        '''
        def convert_to_mod_fn(pv_pair):
            p, v = pv_pair
            if p == '_site_':
                return ModBuilder.ModFn(configure_site, v)
            if p == '_calibsite_': 
                return ModBuilder.ModFn(set_calibration_site, v)
            return ModBuilder.ModFn(DTKConfigBuilder.set_param, p, v)

        return ModBuilder.set_mods([convert_to_mod_fn(pv_pair) for pv_pair in pv_pairs])
