import os
import unittest
import dtk.commands
from argparse import Namespace
import tempfile
from simtools.Utilities.General import rmtree_f
from simtools.DataAccess.DataStore import DataStore
import simtools.Utilities.disease_packages as disease_packages

class TestCommands(unittest.TestCase):
    TEST_FILE_NAME = 'inputfile1'
    TEST_FILE_CONTENTS = {
        'v1.0': '1.0 \n',
        'v1.2': '1.2\n'
    }

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        rmtree_f(self.tempdir)

    def test_list_packages(self):
        args = {
            'is_test': True
        }
        namespace = self.init_namespace(args)
        packages = dtk.commands.list_packages(args=namespace, unknownArgs=None)
        self.assertTrue(isinstance(packages, list))
        self.assertTrue(packages.__contains__(disease_packages.TEST_DISEASE_PACKAGE_NAME))

    def test_list_package_versions(self):
        # positive test
        args = {
            'package_name': disease_packages.TEST_DISEASE_PACKAGE_NAME
        }
        namespace = self.init_namespace(args)
        versions = dtk.commands.list_package_versions(args=namespace, unknownArgs=None)
        self.assertTrue(isinstance(versions, list))
        self.assertEqual(2, len(versions))
        self.assertEqual(['v1.0', 'v1.2'], sorted(versions))

        # negative test
        args = {
            'package_name': 'notapackage'
        }
        namespace = self.init_namespace(args)
        versions = dtk.commands.list_package_versions(args=namespace, unknownArgs=None)
        self.assertEqual(0, len(versions))

    def test_get_package(self):
        workspace = self.tempdir

        # no existing version, default version obtained
        # ... and NO local package directory
        package_name = disease_packages.TEST_DISEASE_PACKAGE_NAME
        args = {
            'package_name': package_name,
            'package_version': 'latest',
            'dest': workspace,
        }
        namespace = self.init_namespace(args)
        dtk.commands.get_package(args=namespace, unknownArgs=None)
        package_dir = os.path.join(workspace, package_name)
        self.assertTrue(os.path.exists(workspace))
        self.assertTrue(os.path.exists(package_dir))
        self.assertGreaterEqual(len(os.listdir(package_dir)), 0)
        # check a specific file for proper contents
        test_file = os.path.join(package_dir, self.TEST_FILE_NAME)
        contents = self.get_file_contents(test_file)
        self.assertEqual(self.TEST_FILE_CONTENTS['v1.2'], contents)
        # check DB status
        db_key = disease_packages.construct_package_version_db_key(package_name)
        self.assertEqual('v1.2', DataStore.get_setting(db_key).value)

        # preexisting version, specified version obtained
        package_name = disease_packages.TEST_DISEASE_PACKAGE_NAME
        args = {
            'package_name': package_name,
            'package_version': 'v1.0',
            'dest': workspace
        }
        namespace = self.init_namespace(args)
        dtk.commands.get_package(args=namespace, unknownArgs=None)
        package_dir = os.path.join(workspace, package_name)
        self.assertTrue(os.path.exists(workspace))
        self.assertTrue(os.path.exists(package_dir))
        self.assertGreaterEqual(len(os.listdir(package_dir)), 0)
        # check a specific file for proper contents
        test_file = os.path.join(package_dir, self.TEST_FILE_NAME)
        contents = self.get_file_contents(test_file)
        self.assertEqual(self.TEST_FILE_CONTENTS['v1.0'], contents)
        # check DB status
        db_key = db_key = disease_packages.construct_package_version_db_key(package_name)
        self.assertEqual('v1.0', DataStore.get_setting(db_key).value)

        # specified package exists, but version does not
        package_name = disease_packages.TEST_DISEASE_PACKAGE_NAME
        db_key = db_key = disease_packages.construct_package_version_db_key(package_name)
        original_version = DataStore.get_setting(db_key).value
        args = {
            'package_name': package_name,
            'package_version': 'notaversion',
            'dest': workspace
        }
        namespace = self.init_namespace(args)
        dtk.commands.get_package(args=namespace, unknownArgs=None)
        package_dir = os.path.join(workspace, package_name)
        self.assertTrue(os.path.exists(workspace))
        self.assertTrue(os.path.exists(package_dir))
        self.assertGreaterEqual(len(os.listdir(package_dir)), 0)
        self.assertEqual(original_version, DataStore.get_setting(db_key).value)
        # check a specific file for proper contents
        test_file = os.path.join(package_dir, self.TEST_FILE_NAME)
        contents = self.get_file_contents(test_file)
        self.assertEqual(self.TEST_FILE_CONTENTS['v1.0'], contents)

        # specified package does not exist
        package_name = 'notapackage'
        args = {
            'package_name': package_name,
            'package_version': 'latest',
            'dest': workspace
        }
        namespace = self.init_namespace(args)
        dtk.commands.get_package(args=namespace, unknownArgs=None)
        package_dir = os.path.join(workspace, package_name)
        self.assertFalse(os.path.exists(package_dir))
        # check DB status
        db_key = db_key = disease_packages.construct_package_version_db_key(package_name)
        self.assertEqual(None, DataStore.get_setting(db_key))

    # Helper methods

    # args is a Hash used to set attributes on a Namespace object
    def init_namespace(self, args):
        namespace = Namespace()
        for k, v in args.iteritems():
            setattr(namespace, k, v)
        return namespace

    def get_file_contents(self, filename):
        self.assertTrue(os.path.exists(filename))
        with file(filename) as f:
            text = f.read()
        return text
# class TestCommands

if __name__ == '__main__':
    unittest.main()