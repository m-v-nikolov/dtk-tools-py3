import os
import json
import shutil
import unittest

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.generic.demographics import *
from dtk.vector.larval_habitat import *

class TestDemographics(unittest.TestCase):

    def setUp(self):
        self.cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')

    def tearDown(self):
        pass

    def test_risk(self):
        tmpfile='input/test_risk.json'
        shutil.copyfile('input/test_nodes.json', tmpfile)
        set_risk_mod(tmpfile,'UNIFORM_DISTRIBUTION',0.8,1.2)
        with open(tmpfile,'r') as f:
            j=json.loads(f.read())
        for n in j['Nodes']:
            self.assertEqual(n['IndividualAttributes']['RiskDistribution1'],0.8)
            self.assertEqual(n['IndividualAttributes']['RiskDistribution2'],1.2)
            self.assertEqual(n['IndividualAttributes']['RiskDistributionFlag'],1)
        os.remove(tmpfile)

    def test_immune_mod(self):
        tmpfile='input/test_immune_mod.json'
        shutil.copyfile('input/test_defaults.json', tmpfile)
        set_immune_mod(tmpfile,'GAUSSIAN_DISTRIBUTION',1.0,0.3)
        with open(tmpfile,'r') as f:
            j=json.loads(f.read())
        n=j['Defaults']
        self.assertEqual(n['IndividualAttributes']['ImmunityDistribution1'],1.0)
        self.assertEqual(n['IndividualAttributes']['ImmunityDistribution2'],0.3)
        self.assertEqual(n['IndividualAttributes']['ImmunityDistributionFlag'],2)
        os.remove(tmpfile)

    def test_static(self):
        self.cb.set_param('Demographics_Filenames',['input/test_defaults.json'])
        set_static_demographics(self.cb)
        outfile='input/test_defaults.static.json'
        self.assertListEqual(self.cb.get_param('Demographics_Filenames'),[outfile])
        self.assertEqual(self.cb.get_param('Birth_Rate_Dependence'),'FIXED_BIRTH_RATE')
        with open(outfile,'r') as f:
            j=json.loads(f.read())
        mod_mortality = { "NumDistributionAxes": 2,
                          "AxisNames": [ "gender", "age" ],
                          "AxisUnits": [ "male=0,female=1", "years" ],
                          "AxisScaleFactors": [ 1, 365 ],
                          "NumPopulationGroups": [ 2, 1 ],
                          "PopulationGroups": [ [ 0, 1 ], [ 0 ] ],
                          "ResultUnits": "annual deaths per 1000 individuals",
                          "ResultScaleFactor": 2.74e-06,
                          "ResultValues": [ [ 45 ], [ 45 ] ] }
        n=j['Defaults']
        self.assertDictEqual(n['IndividualAttributes']['MortalityDistribution'],mod_mortality)
        self.assertEqual(n['IndividualAttributes']['AgeDistribution1'],0.000118)
        self.assertEqual(n['IndividualAttributes']['AgeDistributionFlag'],3)
        self.assertEqual(n['NodeAttributes']['BirthRate'],0.12329)
        os.remove(outfile)

    def test_growing(self):
        self.cb.set_param('Demographics_Filenames',['input/test_nodes.json'])
        set_growing_demographics(self.cb)
        outfile='input/test_nodes.growing.json'
        self.assertListEqual(self.cb.get_param('Demographics_Filenames'),[outfile])
        self.assertEqual(self.cb.get_param('Birth_Rate_Dependence'),'POPULATION_DEP_RATE')
        with open(outfile,'r') as f:
            j=json.loads(f.read())
        mod_mortality = { "NumDistributionAxes": 2,
                          "AxisNames": [ "gender", "age" ],
                          "AxisUnits": [ "male=0,female=1", "years" ],
                          "AxisScaleFactors": [ 1, 365 ],
                          "NumPopulationGroups": [ 2, 5 ],
                          "PopulationGroups": [ [ 0, 1 ],
                                                [ 0, 2, 10, 100, 2000 ] ],
                          "ResultUnits": "annual deaths per 1000 individuals",
                          "ResultScaleFactor": 2.74e-06,
                          "ResultValues": [ [ 60, 8, 2, 20, 400 ],
                                            [ 60, 8, 2, 20, 400 ] ] }
        for n in j['Nodes']:
            self.assertDictEqual(n['IndividualAttributes']['MortalityDistribution'],mod_mortality)
            self.assertEqual(n['NodeAttributes']['BirthRate'],0.0001)
        os.remove(outfile)

    def test_habitat_overlay(self):
        set_habitat_multipliers(self.cb, 'single_test_guess_2.5arcmin',
                                [ NodesMultipliers(nodes=[340461476],multipliers={'ALL_HABITATS':10.0}) ])
        overlay=self.cb.demog_overlays['single_test_guess_2.5arcmin']
        self.assertEqual(overlay['Metadata']['IdReference'],'Gridded world grump2.5arcmin')

        with open('input/test_overlay.json') as f:
            j=json.loads(f.read())
        self.assertListEqual(j['Nodes'],overlay['Nodes'])

        set_habitat_multipliers(self.cb, 'single_test_guess_30arcsec',
                                [ NodesMultipliers(nodes=[1632117296],multipliers={'ALL_HABITATS':1.0}) ])
        self.assertEqual(self.cb.demog_overlays['single_test_guess_30arcsec']['Metadata']['IdReference'],'Gridded world grump30arcsec')

if __name__ == '__main__':
    unittest.main()