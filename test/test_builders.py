import unittest

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.utils.builders.sweep import *

class TestBuilders(unittest.TestCase):

    def setUp(self):
        Builder.metadata={}
        self.cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')

    def tearDown(self):
        pass

    def test_param_fn(self):
        k,v=('Simulation_Duration',100)
        fn=Builder.param_fn(k,v)
        fn(self.cb)
        self.assertEqual(self.cb.get_param(k),v)
        self.assertEqual(Builder.metadata,{k:v})

    def test_site_fn(self):
        s='Namawala'
        fn=Builder.site_fn(s)
        fn(self.cb)
        self.assertTrue('Namawala' in self.cb.get_param('Demographics_Filename'))
        self.assertEqual(Builder.metadata,{'_site_':'Namawala'})

    def test_calibsite_fn(self):
        s='Namawala'
        fn=Builder.calib_site_fn(s)
        fn(self.cb)
        self.assertEqual(self.cb.campaign['Events'][0]['Event_Coordinator_Config']['Intervention_Config']['class'],'InputEIR')
        self.assertEqual(self.cb.custom_reports[0].type,'MalariaSummaryReport')
        self.assertEqual(Builder.metadata,{'_site_':'Namawala'})

    def test_vector_param_fn(self):
        s,k,v=('gambiae','Anthropophily',0.8)
        fn=Builder.vector_species_param_changes_fn(s,k,v)
        fn(self.cb)
        self.assertEqual(self.cb.config['parameters']['Vector_Species_Params'][s][k],v)
        self.assertEqual(Builder.metadata,{'gambiae.Anthropophily':v})

    def test_drug_param_fn(self):
        d,k,v=('Artemether','Drug_Cmax',1000)
        fn=Builder.drug_param_changes_fn(d,k,v)
        fn(self.cb)
        self.assertEqual(self.cb.config['parameters']['Malaria_Drug_Params'][d][k],v)
        self.assertEqual(Builder.metadata,{'Artemether.Drug_Cmax':v})

    def test_default(self):
        b=DefaultSweepBuilder()
        ngenerated=0
        for ml in b.mod_generator:
            self.assertEqual(ml,[])
            self.assertEqual(b.metadata,{})
            ngenerated+=1
        self.assertEqual(ngenerated,1)

    def test_run_number(self):
        b=RunNumberSweepBuilder(nsims=10)
        ngenerated=0
        for i,ml in enumerate(b.mod_generator):
            for m in ml:
                m(self.cb)
            self.assertEqual(b.metadata,{'Run_Number':i})
            self.assertEqual(self.cb.get_param('Run_Number'),i)
            ngenerated+=1
        self.assertEqual(ngenerated,10)

    def test_generic_sweep(self):
        b=builder = GenericSweepBuilder.from_dict({'x_Temporary_Larval_Habitat': [0.05,0.1],
                                                   '_site_'    : ['Namawala','Matsari']})
        md=[(0.05,'Namawala'),(0.05,'Matsari'),(0.1,'Namawala'),(0.1,'Matsari')]
        ngenerated=0
        for i,ml in enumerate(b.mod_generator):
            for m in ml:
                m(self.cb)
            self.assertEqual(b.metadata,dict(zip(('x_Temporary_Larval_Habitat','_site_'),md[i])))
            self.assertEqual(self.cb.get_param('x_Temporary_Larval_Habitat'),md[i][0])
            ngenerated+=1
        self.assertEqual(ngenerated,4)

if __name__ == '__main__':
    unittest.main()