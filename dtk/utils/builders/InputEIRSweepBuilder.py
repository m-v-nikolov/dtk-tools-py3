import itertools
import os
from dtk.vector.input_EIR_by_site import configure_site_EIR

# a class to build an experiment of simulations sweeping study-site, larval habitat, and random seed
class InputEIRSweepBuilder:

    def __init__( self, simlist = [('Namawala', 0.2, 0, 0)], circular_shift=False):

        self.finished = False
        self.circular_shift = circular_shift
        self.nsims = len(simlist)
        self.sims = iter(simlist)
        self.isim = 0

    @classmethod
    def from_lists(cls, sites, habitats, rands, fTs=[0], circular_shift=False):
        simlist = list(itertools.product(sites, habitats, rands, fTs))
        return cls(simlist, circular_shift)

    def next_sim(self, config_builder):

        (site, habitat, rand, fT) = self.sims.next()
        #print('site: %s, habitat=%0.1f, rand=%d' % (site, habitat, rand))
        self.build_sweep_site(site, habitat, rand, fT, config_builder)
        self.end_next_sim(config_builder)

    def build_sweep_site(self, site, habitat, rand, fT, config_builder):

        shift = rand if self.circular_shift else 0
        siteConfig=configure_site_EIR(config_builder, site, habitat, shift, fT)

        self.next_params = {'Config_Name': site + '_x_' + str(habitat) + '_fT_' + str(siteConfig['fT']),
                            'Run_Number': rand,
                            'fT': siteConfig['fT'],
                            'monthlyEIRs': siteConfig['monthlyEIRs'],
                            'Demographics_Filename': config_builder.get_param('Demographics_Filename')
                            }

    def end_next_sim(self, config_builder):

        config_builder.update_params(self.next_params)

        self.isim += 1
        if self.isim == self.nsims:
            self.finished = True
