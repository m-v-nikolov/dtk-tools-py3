import itertools
import os
from dtk.vector.study_sites import configure_site
import dtk.generic.demographics as demographics

# a class to build an experiment of simulations sweeping study-site, migration rate, and random seed
class MigrationRateSweepBuilder:

    def __init__( self,
                  simlist = [('Gwembe2Node', 0.2, 0)],
                  input_files = {} ):

        self.finished = False
        self.nsims = len(simlist)
        self.sims = iter(simlist)
        self.isim = 0
        self.geography = input_files.get('geography','')
        self.immune_mod = input_files.get('immune_mod',())
        self.recompile = input_files.get('recompile',False)
        self.immune_init = input_files.get('immune_init',[]) # list of tags (i.e. the bit after 'immune_init_' e.g. 'Sinazongwe_x_0.2')
        self.input_root = input_files.get('input_root',False)

    @classmethod
    def from_lists(cls, sites, migrations, rands, input_files={}):
        simlist = list(itertools.product(sites, migrations, rands))
        return cls(simlist, input_files)

    @classmethod
    def from_tuples(cls, sites, rands, input_files={}):
        simlist = [ (a[0][0], a[0][1], a[1]) for a in list(itertools.product(sites, rands))]
        return cls(simlist, input_files)

    def next_sim(self, config_builder):

        (site, migration, rand) = self.sims.next()
        #print('site: %s, migration=%0.1f, rand=%d' % (site, migration, rand))
        self.build_sweep_site(site, migration, rand, config_builder)
        self.end_next_sim(config_builder)

    def build_sweep_site(self, site, migration, rand, config_builder):

        configure_site(config_builder.config, site)

        if self.geography:
            geography = self.geography
        else:
            geography = config_builder.get_param('Geography')

        self.next_params = {'Config_Name': site + '_xmig_' + str(migration),
                            'x_Local_Migration': migration,
                            'Run_Number': rand,
                            'Geography': geography}

        if self.input_root and self.immune_init:
            # Do this part last, so other modifications to demographics file
            # do not overwite the addition of the immune-initialization file
            demographics.add_immune_overlays(self.input_root, 
                                            geography, 
                                            config_builder.config, 
                                            self.immune_init)

        self.next_params.update({'Demographics_Filename': config_builder.get_param('Demographics_Filename')})

    def end_next_sim(self, config_builder):

        config_builder.update_params(self.next_params)

        self.isim += 1
        if self.isim == self.nsims:
            self.finished = True