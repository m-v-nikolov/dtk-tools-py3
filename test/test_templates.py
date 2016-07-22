import json
import unittest

import sys
from dtk.utils.builders.BaseTemplate import BaseTemplate


class TestBaseTemplate(unittest.TestCase):
    def setUp(self):
        template_content = json.load(open('input/campaign_template.json', 'rb'))
        self.bt = BaseTemplate('campaign_template.json', template_content)

    def test_basics(self):
        # Test the from_file
        template_from_file = BaseTemplate.from_file('input/campaign_template.json')
        self.assertEqual(template_from_file.contents, self.bt.contents)
        self.assertEqual(template_from_file.filename, self.bt.filename)

        # Test get_filename
        self.assertEqual(self.bt.get_filename(), 'campaign_template.json')

        # Test get_contents
        contents = json.load(open('input/campaign_template.json', 'rb'))
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

    def test_get_param(self):
        # Test some parameter retrieval
        self.assertEqual(self.bt.get_param('Events.0.class'), ('Events.0.class', 'CampaignEventByYear'))
        self.assertEqual(self.bt.get_param('Events[1].Start_Year'), ('Events[1].Start_Year', 1985))
        self.assertEqual(self.bt.get_param('Campaign_Name'), ('Campaign_Name', "4E_Health_Care_Model_Baseline"))
        self.assertEqual(self.bt.get_param('Events[2].Nodeset_Config'), ('Events[2].Nodeset_Config', {"class": "NodeSetAll"}))

    def test_set_param(self):
        # self.bt.set_param('Campaign_Name','test')
        param, value = self.bt.get_param_handle('Campaign_Name')
        param[value] = 'test'
        self.assertEqual(self.bt.contents['Campaign_Name'], 'test')
        self.bt.set_param('Events[1].Start_Year', 1900)
        self.assertEqual(self.bt.contents['Events'][1]['Start_Year'], 1900)
        self.bt.set_param('Events[2].Nodeset_Config', {"class": "NodeSetAll1"})
        self.assertEqual(self.bt.contents['Events'][2]['Nodeset_Config']['class'], 'NodeSetAll1')

    def test_cast_value(self):
        self.assertTrue(isinstance(self.bt.cast_value('1'), int))
        self.assertTrue(isinstance(self.bt.cast_value('1.5'), float))
        self.assertTrue(isinstance(self.bt.cast_value('test'), str))
        self.assertTrue(isinstance(self.bt.cast_value({'a':'b'}), dict))
        self.assertTrue(isinstance(self.bt.cast_value((1,2,3)), tuple))
        self.assertTrue(isinstance(self.bt.cast_value([1,2,3]), list))


if __name__ == '__main__':
    unittest.main()
