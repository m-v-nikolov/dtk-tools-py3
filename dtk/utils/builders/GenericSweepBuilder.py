import itertools
import os
from dtk.vector.study_sites import configure_site
import dtk.generic.demographics as demographics

# a class to build an experiment of simulations sweeping study-site, larval habitat, and random seed
class GenericSweepBuilder:

    def __init__( self,
                  paramnames = ['site', 'x_Temporary_Larval_Habitat', 'Run_Number'],
                  simlist = [('Namawala', 0.2, 0)],
                  input_files = {} ):

        self.finished = False
        self.nsims = len(simlist)
        self.simparams = paramnames; 
        self.sims = iter(simlist)
        self.isim = 0
        self.geography = input_files.get('geography','')
        self.immune_mod = input_files.get('immune_mod',())
        self.recompile = input_files.get('recompile',False)
        self.immune_init = input_files.get('immune_init',False)
        self.input_root = input_files.get('input_root',False)

    @classmethod
    def from_dict(cls, sweep_params, input_files = {}):
        sitelist = sweep_params.pop('site')
        runnumbers = sweep_params.pop('Run_Number')
        paramvals = tuple(sweep_params.values())
        simlist = list(itertools.product(sitelist, runnumbers, *paramvals))
        paramnames = ['site'] + ['Run_Number'] + sweep_params.keys()
        return cls(paramnames, simlist, input_files)
    
    def next_sim(self, config_builder):

        nextvals = self.sims.next()
        #print('site: %s, habitat=%0.1f, rand=%d' % (site, habitat, rand))
        self.build_sweep_site(nextvals, config_builder)
        self.end_next_sim(config_builder)

    def build_sweep_site(self, nextvals, config_builder):

        site = nextvals[0]
        configure_site(config_builder.config, site)

        if self.geography:
            geography = self.geography
        else:
            geography = config_builder.get_param('Geography')

        

        self.next_params = dict(zip(self.simparams[1:], nextvals[1:]))
        self.next_params['Geography'] = geography
        
        self.next_params['Config_Name'] = site+'_'+'_'.join(map('_'.join, zip(self.simparams[2:], map(str, nextvals[2:]))))
        print self.next_params['Config_Name']
        
##        self.next_params = {'Config_Name': site + '_x_' + str(habitat),
##                            'x_Temporary_Larval_Habitat': habitat,
##                            'Run_Number': rand,
##                            'Geography': geography}

        if self.input_root:
            if self.immune_mod:
                self.next_params.update({'Immunity_Distribution': list(self.immune_mod)})
                if self.recompile:
                    demographics.set_immune_mod( os.path.join(
                                                    self.input_root, 
                                                    geography, 
                                                    config_builder.get_param('Demographics_Filename').replace("compiled.","",1)),
                                                *self.immune_mod )

            demographics.set_static_demographics(self.input_root, 
                                                 config_builder.config, 
                                                 geography, 
                                                 recompile=self.recompile)

            if self.immune_init:
                # Do this part last, so other modifications to demographics file
                # do not overwite the addition of the immune-initialization file
                demographics.add_immune_init(self.input_root, 
                                             geography, 
                                             config_builder.config, 
                                             site, 
                                             habitat)
                
        self.next_params.update({'Demographics_Filename': config_builder.get_param('Demographics_Filename')})

    def end_next_sim(self, config_builder):

        config_builder.update_params(self.next_params)

        self.isim += 1
        if self.isim == self.nsims:
            self.finished = True
