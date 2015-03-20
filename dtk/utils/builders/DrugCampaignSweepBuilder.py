import itertools
from StudySiteSweepBuilder import StudySiteSweepBuilder

# a class derived from StudySiteSweepBuilder 
# that additionally sweeps on drug-campaign parameters
class DrugCampaignSweepBuilder(StudySiteSweepBuilder):

    def __init__( self, simlist, add_event_fn, drug_code, start_days, input_files):
        StudySiteSweepBuilder.__init__(self, simlist, input_files)
        self.add_event_fn = add_event_fn
        self.drug_code = drug_code
        self.start_days = start_days

    @classmethod
    def from_lists(cls, sites, habitats, coverages, rands, add_event_fn, drug_code, start_days=[], input_files={}):
        simlist = list(itertools.product(sites, habitats, coverages, rands))
        return cls(simlist, add_event_fn, drug_code, start_days, input_files)

    @classmethod
    def from_tuples(cls, sites, coverages, rands, add_event_fn, drug_code, start_days=[], input_files={}):
        simlist = [ (a[0][0], a[0][1], a[1], a[2]) for a in list(itertools.product(sites, coverages, rands))]
        return cls(simlist, add_event_fn, drug_code, start_days, input_files)

    def next_sim(self, config_builder):

        (site, habitat, coverage, rand) = self.sims.next()
        #print('site: %s, habitat=%0.1f, coverage=%0.2f, rand=%d' % (site, habitat, coverage, rand))

        self.build_sweep_site(site, habitat, rand, config_builder)

        self.add_event_fn(config_builder, drug_code = self.drug_code, coverage = coverage, start_days=self.start_days)
        config_name = self.next_params['Config_Name']
        self.next_params.update({'Config_Name': config_name + '_' + self.drug_code + '_' + str(int(100*coverage)) + "pct",
                                 'Demographic_Coverage': coverage,
                                 'Drug_Code': self.drug_code})

        self.end_next_sim(config_builder)
