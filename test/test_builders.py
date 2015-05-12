import unittest

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.utils.builders.sweep import *
from dtk.vector.species import get_species_param,set_species_param
from dtk.interventions.malaria_drugs import get_drug_param,set_drug_param

class TestBuilders(unittest.TestCase):

    def setUp(self):
        Builder.metadata={}
        self.cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')

    def tearDown(self):
        pass

    def test_param_fn(self):
        k,v=('Simulation_Duration',100)
        fn=param_fn(k,v)
        fn(self.cb)
        self.assertEqual(self.cb.get_param(k),v)
        self.assertEqual(Builder.metadata,{k:v})

    def test_site_fn(self):
        s='Namawala'
        fn=site_fn(s)
        fn(self.cb)
        self.assertTrue('Namawala' in self.cb.get_param('Demographics_Filenames')[0])
        self.assertEqual(Builder.metadata,{'_site_':'Namawala'})

    def test_calibsite_fn(self):
        s='Namawala'
        fn=site_fn(s,calib=True)
        fn(self.cb)
        self.assertEqual(self.cb.campaign['Events'][0]['Event_Coordinator_Config']['Intervention_Config']['class'],'InputEIR')
        self.assertEqual(self.cb.custom_reports[0].type,'MalariaSummaryReport')
        self.assertEqual(Builder.metadata,{'_site_':'Namawala'})

    def test_custom_fn(self):
        fn=custom_fn('gambiae.Required_Habitat_Factor',
                     set_species_param,'gambiae','Required_Habitat_Factor',
                     value=[100,50])
        fn(self.cb)
        self.assertListEqual(get_species_param(self.cb,'gambiae','Required_Habitat_Factor'),[100,50])

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

    def test_vector_drug_param_sweep(self):
        b = GenericSweepBuilder.from_dict({
              '_gambiae.Required_Habitat_Factor_': [(set_species_param,'gambiae','Required_Habitat_Factor',dict(value=v)) for v in ((100,50),(200,100))],
              '_Artemether.Max_Drug_IRBC_Kill': [(set_drug_param,'Artemether','Max_Drug_IRBC_Kill',dict(value=v)) for v in (4.0,2.0)]
              })
        md=[(4,(100,50)),(4,(200,100)),(2,(100,50)),(2,(200,100))]
        ngenerated=0
        for i,ml in enumerate(b.mod_generator):
            for m in ml: 
                m(self.cb)
            self.assertListEqual([v['value'] for v in b.metadata.values()],list(md[i]))
            self.assertEqual(get_species_param(self.cb,'gambiae','Required_Habitat_Factor'),md[i][1])
            self.assertEqual(get_drug_param(self.cb,'Artemether','Max_Drug_IRBC_Kill'),md[i][0])
            ngenerated+=1
        self.assertEqual(ngenerated,4)

if __name__ == '__main__':
    unittest.main()