import unittest

from simtools.Utilities.LocalOS import LocalOS

class TestLocalOS(unittest.TestCase):

    def test_works_on_this_system(self):
        for param in ['name', 'username']:
            self.assertTrue(hasattr(LocalOS, param))
            attr = getattr(LocalOS, param)
            self.assertFalse(callable(attr))
            self.assertTrue(isinstance(attr, str))
            self.assertTrue(len(attr) > 0)

if __name__ == '__main__':
    unittest.main()
