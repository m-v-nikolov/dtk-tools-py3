import json
import unittest

import sys
from dtk.utils.builders.BaseTemplate import BaseTemplate
from dtk.utils.builders.ConfigTemplate import ConfigTemplate
from dtk.utils.builders.TaggedTemplate import TaggedTemplate
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


class TestTaggedTemplate(unittest.TestCase):
    def setUp(self):
        self.campaign_tpl = 'input/templates/campaign_template_simple.json'
        self.tt = TaggedTemplate.from_file(self.campaign_tpl)

    def test_basics(self):
        # The tag is defaulted properly
        self.assertEqual(self.tt.tag,"__KP")
        # We found the correct ones
        self.assertEqual(self.tt.tag_dict.keys()[0],'_Seeding_15_24_Male')
        self.assertEqual(self.tt.tag_dict.keys()[1],'_Seeding_Year')
        self.assertEqual(self.tt.tag_dict.keys()[2],'_STI_CoInfection_At_Debut')
        # The file has been correctly read
        campaign = json.load(open(self.campaign_tpl,'rb'))
        self.assertEqual(self.tt.contents,campaign)
        self.assertEqual(self.tt.filename,'campaign_template_simple.json')

    def test_get_param(self):
        # Test that the tags are actually retrieved properly
        kpyears = self.tt.get_param('Start_Year__KP_Seeding_Year')
        self.assertEqual(kpyears[1], [1981, 1982, 1983, 1984])
        self.assertEqual(kpyears[0], ['Events.0.Start_Year', 'Events.1.Start_Year', 'Events.2.Start_Year', 'Events.3.Start_Year'])

        kpdemcov = self.tt.get_param('Demographic_Coverage__KP_Seeding_15_24_Male')
        self.assertEqual(kpdemcov[1], [0.03,0.05])
        self.assertEqual(kpdemcov[0], ['Events.0.Event_Coordinator_Config.Demographic_Coverage', 'Events.2.Event_Coordinator_Config.Demographic_Coverage'])

        kpintconf = self.tt.get_param('Intervention_Config__KP_STI_CoInfection_At_Debut')
        self.assertEqual(kpintconf[1], [{"class": "NodeLevelHealthTriggeredIV","Actual_IndividualIntervention_Config":{"New_STI_CoInfection_Status": 1}}])
        self.assertEqual(kpintconf[0], ['Events.4.Event_Coordinator_Config.Intervention_Config'])

    def test_set_param(self):
        # Test setting tag values
        self.tt.set_param('Start_Year__KP_Seeding_Year',100)
        self.assertEqual(self.tt.contents['Events'][0]['Start_Year'], 100)
        self.assertEqual(self.tt.contents['Events'][1]['Start_Year'], 100)
        self.assertEqual(self.tt.contents['Events'][2]['Start_Year'], 100)
        self.assertEqual(self.tt.contents['Events'][3]['Start_Year'], 100)

        # Lets try setting a more complicated value
        self.tt.set_param('Start_Year__KP_Seeding_Year', [1,2,3])
        self.assertEqual(self.tt.contents['Events'][0]['Start_Year'], [1,2,3])
        self.assertEqual(self.tt.contents['Events'][1]['Start_Year'], [1,2,3])
        self.assertEqual(self.tt.contents['Events'][2]['Start_Year'], [1,2,3])
        self.assertEqual(self.tt.contents['Events'][3]['Start_Year'], [1,2,3])

        # Lets try setting an even more complicated value
        self.tt.set_param('Start_Year__KP_Seeding_Year', {'a':{'b':{'c':[1,2,3]}}})
        self.assertEqual(self.tt.contents['Events'][0]['Start_Year'], {'a':{'b':{'c':[1,2,3]}}})
        self.assertEqual(self.tt.contents['Events'][1]['Start_Year'], {'a':{'b':{'c':[1,2,3]}}})
        self.assertEqual(self.tt.contents['Events'][2]['Start_Year'], {'a':{'b':{'c':[1,2,3]}}})
        self.assertEqual(self.tt.contents['Events'][3]['Start_Year'], {'a':{'b':{'c':[1,2,3]}}})

    def test_expand_tag(self):
        self.assertEqual(self.tt.expand_tag('Start_Year__KP_Seeding_Year'), ['Events.0.Start_Year', 'Events.1.Start_Year', 'Events.2.Start_Year', 'Events.3.Start_Year'])
        self.assertEqual(self.tt.expand_tag('Demographic_Coverage__KP_Seeding_15_24_Male'), ['Events.0.Event_Coordinator_Config.Demographic_Coverage', 'Events.2.Event_Coordinator_Config.Demographic_Coverage'])
        self.assertEqual(self.tt.expand_tag('Intervention_Config__KP_STI_CoInfection_At_Debut'), ['Events.4.Event_Coordinator_Config.Intervention_Config'])
        self.assertEqual(self.tt.expand_tag('doesnt_exist'), [])


if __name__ == '__main__':
    unittest.main()
