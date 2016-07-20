import unittest

from simtools.SetupParser import SetupParser
from pyCOMPS import pyCOMPS
from COMPS import Client


class TestIniFile(unittest.TestCase):
    # def setUp(self):
    #     print "Successfully loaded ini file"

    def test_get_attributes(self):
        ini = SetupParser(None, 'ini\\test_simtools.ini', False)
        max_threads = ini.get('max_threads')
        self.assertEqual(max_threads, '16')

    def test_get_exception_for_missing_section(self):
        ini = SetupParser(None, 'ini\\test_simtools.ini', False)
        none = None

        try:
            none = ini.get('aaa')
        except:
            self.assertIsNone(none)

    def test_comps_attribute_validation(self):
        ini = SetupParser("HPC", 'ini\\test_simtools.ini', True, "HPC", False)
        Client.Login(ini.get('server_endpoint'))

        ini.validate("HPC", ini)

    def test_local_section_attribute_validation(self):
        ini = SetupParser("LOCAL", 'ini\\test_simtools.ini', True, None, False)
        ini.validate("LOCAL", ini)

if __name__ == '__main__':
    unittest.main()
