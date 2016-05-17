import unittest

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder


class TestConfigBuilder(unittest.TestCase):

    def setUp(self):
        self.cb = DTKConfigBuilder.from_defaults('MALARIA_SIM', Base_Air_Temperature=26)

    def test_kwargs(self):
        self.assertEqual(self.cb.get_param('Base_Air_Temperature'), 26)

    def test_enable_disable(self):
        self.cb.disable('Demographics_Birth')
        self.assertEqual(self.cb.get_param('Enable_Demographics_Birth'), 0)
        self.cb.enable('Demographics_Birth')
        self.assertEqual(self.cb.get_param('Enable_Demographics_Birth'), 1)

class TestConfigExceptions(unittest.TestCase):

    def test_bad_kwargs(self):
        self.assertRaises(Exception, lambda: DTKConfigBuilder.from_defaults('MALARIA_SIM', Not_A_Climate_Parameter=26))

    def test_bad_simtype(self):
        self.assertRaises(Exception, lambda: DTKConfigBuilder.from_defaults('NOT_A_SIM'))    


if __name__ == '__main__':
    unittest.main()
