import os
import unittest
import dtk.commands
from argparse import Namespace
import tempfile
from simtools.DataAccess.DataStore import DataStore
from simtools.Utilities.General import rmtree_f
from simtools.Utilities.GitHub.GitHub import DTKGitHub

class TestCommands(unittest.TestCase):
    TEST_FILE_NAME = 'inputfile1'
    TEST_FILE_CONTENTS = {
        'v1.0': '1.0 \n',
        'v1.2': '1.2\n'
    }

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_list_packages(self):
        args = {'quiet': True}
        namespace = self.init_namespace(args)
        packages = dtk.commands.list_packages(args=namespace, unknownArgs=None)
        self.assertTrue(isinstance(packages, list))
        self.assertTrue('malaria' in packages)

    def test_list_package_versions(self):
        # positive test
        args = {
            'package_name': DTKGitHub.TEST_DISEASE_PACKAGE_NAME,
            'quiet': True
        }
        namespace = self.init_namespace(args)
        versions = dtk.commands.list_package_versions(args=namespace, unknownArgs=None)
        self.assertTrue(isinstance(versions, list))
        self.assertEqual(4, len(versions))
        self.assertEqual(['1.0.0', '1.0.1', '1.2.0', '2.0.1'], sorted(versions))

        # negative test
        args = {
            'package_name': 'notapackage',
            'quiet': True
        }
        namespace = self.init_namespace(args)
        kwargs = {'args': namespace, 'unknownArgs': None}
        self.assertRaises(DTKGitHub.UnknownRepository, dtk.commands.list_package_versions, **kwargs)

    def verify_package_download(self, source_dir, expected_version):
        test_data_pattern = "I am a file belonging to version %s .\n"

        # verify the setup.py file points to the right version that would be installed
        setup_filename = os.path.join(source_dir, 'setup.py')
        self.assertTrue(os.path.isfile(setup_filename))
        with open(setup_filename, 'r') as file:
            data = file.read()
            expected_string = 'version=\'%s\'' % expected_version
            self.assertTrue(expected_string in data)

        # test contents of a specific file
        test_file = os.path.join(source_dir, 'module1', 'test.py')
        expected_data = test_data_pattern % expected_version
        self.assertTrue(os.path.isfile(test_file))
        with open(test_file, 'r') as file:
            test_data = file.read()
            self.assertEqual(test_data, expected_data)

    def test_get_package(self):
        # This test does NOT test installation, but it does test that the appropriate setup occurs prior
        # to pip install

        # for case each, verify:
        # - setup.py has the right version string
        # - data in a sample file is correct

        package_name = DTKGitHub.TEST_DISEASE_PACKAGE_NAME

        # no version specified, get latest (2.0.1)
        args = {
            'is_test': True,
            'package_name': package_name,
            'package_version': 'latest'
        }
        namespace = self.init_namespace(args)
        source_dir = dtk.commands.get_package(args=namespace, unknownArgs=None)
        self.verify_package_download(source_dir=source_dir, expected_version='2.0.1')

        # version specified, get it!
        expected_version = '1.0.1'
        args = {
            'is_test': True,
            'package_name': package_name,
            'package_version': expected_version
        }
        namespace = self.init_namespace(args)
        source_dir = dtk.commands.get_package(args=namespace, unknownArgs=None)
        self.verify_package_download(source_dir=source_dir, expected_version=expected_version)

        package_name = 'notapackage'
        args = {
            'is_test': True,
            'package_name': package_name,
            'package_version': 'latest',
        }
        namespace = self.init_namespace(args)
        kwargs = {'args': namespace, 'unknownArgs': None}
        self.assertRaises(DTKGitHub.UnknownRepository, dtk.commands.get_package, **kwargs)

    # Helper methods

    # args is a Hash used to set attributes on a Namespace object
    def init_namespace(self, args):
        namespace = Namespace()
        for k, v in args.items():
            setattr(namespace, k, v)
        return namespace

    def get_file_contents(self, filename):
        self.assertTrue(os.path.exists(filename))
        with open(filename, "r") as f:
            text = f.read()
        return text
# class TestCommands

if __name__ == '__main__':
    unittest.main()