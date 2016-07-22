import json
import unittest

import sys
from dtk.utils.builders.BaseTemplate import BaseTemplate
from dtk.utils.builders.ConfigTemplate import ConfigTemplate
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder


class TestBaseTemplate(unittest.TestCase):
    def setUp(self):
        self.campaign_tpl = 'input/templates/campaign_template.json'
        template_content = json.load(open(self.campaign_tpl, 'rb'))
        self.bt = BaseTemplate('campaign_template.json', template_content)

    def test_basics(self):
        # Test the from_file
        template_from_file = BaseTemplate.from_file(self.campaign_tpl)
        self.assertEqual(template_from_file.contents, self.bt.contents)
        self.assertEqual(template_from_file.filename, self.bt.filename)

        # Test get_filename
        self.assertEqual(self.bt.get_filename(), 'campaign_template.json')

        # Test get_contents
        contents = json.load(open(self.campaign_tpl, 'rb'))
        self.assertEqual(self.bt.get_contents(), contents)

    def test_has_params(self):
        # Test some parameter existence
        self.assertTrue(self.bt.has_param('Campaign_Name'))
        self.assertTrue(self.bt.has_param('Events[0]'))
        self.assertTrue(self.bt.has_param('Events[0].Event_Coordinator_Config.Target_Demographic'))
        self.assertTrue(self.bt.has_param('Events[0].Event_Coordinator_Config.Demographic_Coverage__KP_Seeding_15_24_Male'))
        self.assertFalse(self.bt.has_param('Events[50]'))
        self.assertFalse(self.bt.has_param('Events1[50]'))
        self.assertFalse(self.bt.has_param('DUMMY_PARAM'))
        self.assertTrue(self.bt.has_param('Events.1'))

    def test_get_param(self):
        # Test some parameter retrieval
        self.assertEqual(self.bt.get_param('Events.0.class'), ('Events.0.class', 'CampaignEventByYear'))
        self.assertEqual(self.bt.get_param('Events[1].Start_Year'), ('Events[1].Start_Year', 1985))
        self.assertEqual(self.bt.get_param('Campaign_Name'), ('Campaign_Name', "4E_Health_Care_Model_Baseline"))
        self.assertEqual(self.bt.get_param('Events[2].Nodeset_Config'), ('Events[2].Nodeset_Config', {"class": "NodeSetAll"}))
        self.assertEqual(self.bt.get_param('Events.1')[1]['class'], 'CampaignEventByYear')

    def test_set_param(self):
        # self.bt.set_param('Campaign_Name','test')
        param, value = self.bt.get_param_handle('Campaign_Name')
        param[value] = 'test'
        self.assertEqual(self.bt.contents['Campaign_Name'], 'test')
        self.bt.set_param('Events[1].Start_Year', 1900)
        self.assertEqual(self.bt.contents['Events'][1]['Start_Year'], 1900)
        self.bt.set_param('Events[2].Nodeset_Config', {"class": "NodeSetAll1"})
        self.assertEqual(self.bt.contents['Events'][2]['Nodeset_Config']['class'], 'NodeSetAll1')
        self.bt.set_param('Events[2]', {"class": "NodeSetAll1"})
        self.assertEqual(self.bt.contents['Events'][2]['class'], 'NodeSetAll1')

    def test_set_params(self):
        params = {
            'Campaign_Name':'test2',
            'Events[2].Start_Year':1910,
            'Events.1.Start_Year':1910,
            'Events[3]':{'test':'test2'},
            'Events[4]':[1,2,3]
        }
        self.bt.set_params(params)
        self.assertEqual(self.bt.contents['Campaign_Name'], 'test2')
        self.assertEqual(self.bt.contents['Events'][2]['Start_Year'], 1910)
        self.assertEqual(self.bt.contents['Events'][1]['Start_Year'], 1910)
        self.assertEqual(self.bt.contents['Events'][3], {'test':'test2'})
        self.assertEqual(self.bt.contents['Events'][4], [1,2,3])

    def test_cast_value(self):
        self.assertTrue(isinstance(self.bt.cast_value('1'), int))
        self.assertTrue(isinstance(self.bt.cast_value('1.5'), float))
        self.assertTrue(isinstance(self.bt.cast_value('test'), str))
        self.assertTrue(isinstance(self.bt.cast_value({'a':'b'}), dict))
        self.assertTrue(isinstance(self.bt.cast_value((1,2,3)), tuple))
        self.assertTrue(isinstance(self.bt.cast_value([1,2,3]), list))


class TestConfigTemplate(unittest.TestCase):
    def setUp(self):
        self.config_tpl='input/templates/config_template.json'
        self.ct = ConfigTemplate.from_file(self.config_tpl)

    def test_class(self):
        contents = json.load(open(self.config_tpl,'rb'))
        self.assertEqual(self.ct.contents,contents['parameters'])
        self.assertEqual(self.ct.get_contents(),contents)

        # Try the params setting and cb
        params = {
            'Air_Temperature_Variance': 0,
            'Vector_Sampling_Type': "NONE",
            'Vector_Species_Names[1]':'farauti',
            'Vector_Species_Params.arabiensis.Larval_Habitat_Types.CONSTANT': 5,
            'Demographics_Filenames.0': "test.json"
        }
        cb = DTKConfigBuilder.from_defaults('VECTOR_SIM')
        self.ct.set_params_and_modify_cb(params,cb)
        self.assertEqual(self.ct.contents['Air_Temperature_Variance'], 0)
        self.assertEqual(cb.get_param('Air_Temperature_Variance'), 0)

        self.assertEqual(self.ct.contents['Vector_Sampling_Type'], 'NONE')
        self.assertEqual(cb.get_param('Vector_Sampling_Type'), 'NONE')

        self.assertEqual(self.ct.contents['Vector_Species_Names'][1], 'farauti')
        self.assertEqual(cb.get_param('Vector_Species_Names')[1], 'farauti')

        self.assertEqual(self.ct.contents['Vector_Species_Params']['arabiensis']['Larval_Habitat_Types']['CONSTANT'], 5)
        self.assertEqual(cb.get_param('Vector_Species_Params')['arabiensis']['Larval_Habitat_Types']['CONSTANT'], 5)

        self.assertEqual(self.ct.contents['Demographics_Filenames'][0], "test.json")
        self.assertEqual(cb.get_param('Demographics_Filenames')[0], "test.json")


if __name__ == '__main__':
    unittest.main()
