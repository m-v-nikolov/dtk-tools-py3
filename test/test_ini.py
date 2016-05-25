import unittest

from simtools.SetupParser import SetupParser


class TestIniFile(unittest.TestCase):
    def setUp(self):
        self.ini = SetupParser("ini\\test_simtools.ini")
        print "Successfully loaded ini file"

    def test_get_attributes(self):
        self.max_threads = self.ini.get('GLOBAL', 'max_threads')
        self.assertEqual(self.max_threads, '16')

    def test_get_exception_for_missing_section(self):
        self.none = None

        try:
            self.none = self.ini.get('JUNK', 'aaa')
        except:
            self.assertIsNone(self.none)

if __name__ == '__main__':
    unittest.main()
