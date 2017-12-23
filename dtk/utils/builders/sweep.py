import itertools

from simtools.ModBuilder import ModBuilder, ModFn
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.vector.study_sites import configure_site


class RunNumberSweepBuilder(ModBuilder):
    def __init__(self, nsims):
        self.tags = {}
        self.mod_generator = (
            self.set_mods(
                [ModFn(DTKConfigBuilder.set_param, 'Run_Number', i)]
            ) for i in range(nsims)
        )


class GenericSweepBuilder(ModBuilder):
    """
    A convenient syntax for simple sweeps over configuration parameters.
    """

    @classmethod
    def from_dict(cls, d):
        """
        Generates lists of functions to override parameters for each combination of values.

        :param d: a dictionary of parameter names to lists of parameter values to sweep over.
        """
        params = d.keys()
        combos = itertools.product(*d.values())
        return cls((cls.set_mods(zip(params, combo)) for combo in combos))

    @classmethod
    def set_mods(cls, pv_pairs):
        """
        Dictionary may include the special keys: '__site__' or '__calibsite___',
        which are recognized as shorthand for site-configuration functions
        with the site name as the "parameter value".
        """
        def convert_to_mod_fn(pv_pair):
            p, v = pv_pair
            if p == '_site_':
                return ModFn(configure_site, v)
            return ModFn(DTKConfigBuilder.set_param, p, v)

        return ModBuilder.set_mods([convert_to_mod_fn(pv_pair) for pv_pair in pv_pairs])

    @classmethod
    def from_list_of_override_dicts(cls, list_of_overrides):
        """
        Each dict is a set of param/value overrides to use in individual simulations
        :param dict_list:
        :return:
        """
        return cls((cls.set_mods(pv_dict.items()) for pv_dict in list_of_overrides))
