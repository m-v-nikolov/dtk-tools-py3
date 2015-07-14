import unittest

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.generic.climate import set_climate_constant

class TestClimate(unittest.TestCase):

    def setUp(self):
        self.cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')

    def tearDown(self):
        pass

    def test_constant_climate(self):
        set_climate_constant(self.cb, Base_Air_Temperature=26, Base_Rainfall=3)
        self.assertEqual(self.cb.get_param('Climate_Model'), 'CLIMATE_CONSTANT')
        self.assertEqual(self.cb.get_param('Base_Air_Temperature'), 26)
        self.assertEqual(self.cb.get_param('Base_Rainfall'), 3)

    def test_bad_climate_param(self):
        self.assertRaises(Exception, lambda: set_climate_constant(self.cb, Not_A_Climate_Parameter=26))

if __name__ == '__main__':
    unittest.main()