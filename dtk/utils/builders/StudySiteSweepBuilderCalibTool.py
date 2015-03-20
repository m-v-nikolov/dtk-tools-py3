import itertools
import os
from dtk.generic.geography_calibration import set_geography_config, set_geography_campaigns


############## immune mod????????????????????

# a class to build an experiment of simulations sweeping study-site
class StudySiteSweepBuilderCalibTool:

    def __init__( self,
                  paramnames = ['site', 'x_Temporary_Larval_Habitat'],
                  simlist = [('Dapelogo', 0.2)]):

        self.finished = False
        self.simparams = paramnames; 
        self.nsims = len(simlist)
        self.sims = iter(simlist)
        self.isim = 0

    @classmethod
    def from_dict(cls, sweep_params, input_files = {}):
        sitelist = sweep_params.pop('site')
        paramvals = tuple(sweep_params.values())
        simlist = list(itertools.product(sitelist, runnumbers, *paramvals))
        paramnames = ['site'] + sweep_params.keys()
        return cls(paramnames, simlist, input_files)
    
    def next_sim(self, config_builder):

        nextvals = self.sims.next()
        self.build_sweep_site(nextvals, config_builder)
        self.end_next_sim(config_builder)

    def build_sweep_site(self, nextvals, config_builder):

        site = nextvals[0]
        set_geography_config(config_builder.config, site)
        set_geography_campaigns(config_builder, site)

        geography = config_builder.get_param('Geography')        

        self.next_params = dict(zip(self.simparams[1:], nextvals[1:]))
        self.next_params['Geography'] = geography
        
        self.next_params['Config_Name'] = site
                        
        self.next_params.update({'Demographics_Filename': config_builder.get_param('Demographics_Filename')})

    def end_next_sim(self, config_builder):

        config_builder.update_params(self.next_params)

        self.isim += 1
        if self.isim == self.nsims:
            self.finished = True


