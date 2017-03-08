import json
import unittest

from simtools.COMPSAccess.Builder import Builder


class TestCOMPS(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_builder(self):
        b = Builder(name='testbuilder', suite_id='123', dynamic_parameters={'p1':[1,2,3], 'p2':[4,5,6]})
        print json.dumps(b.wo, indent=3)

if __name__ == '__main__':
    unittest.main()