import os
import shutil
import tempfile
import unittest

from random import randint
from time import sleep

from simtools.Utilities.GitHub.MultiPartFile import GitHubFile
from simtools.Utilities.GitHub.GitHub import DependencyGitHub
DependencyGitHub.DEFAULT_REPOSITORY_NAME = 'TestRepository'

class TestGitHub(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_case = {
            'single_part': {
                'data': 'abcdefghijklmnopqrstuvwxyz',
                'max_chunk_size': None # default behavior
            },
            'multi_part': {
                'data': 'abcdefghijklmnopqrstuvwxyz',
                'max_chunk_size': 12 # bytes
            }
        }


        self.legacy_file = os.path.join(os.path.dirname(__file__), 'input', 'GitHub', 'testfile.whl')

    def tearDown(self):
        pass

    def test_round_trip(self):
        """
        This tests pushing a file and downloading it, comparing it for data exactness, for both
        single-part and multi-part files.
        :return:
        """
        for case_name, case in self.test_case.iteritems():
            # write the new file to use
            new_file = str(randint(0, 1000000000))
            local_file = os.path.join(self.temp_dir, new_file)
            with open(local_file, 'w') as file:
                file.write(case['data'])
            dependency = GitHubFile(source_filename=local_file)
            if case['max_chunk_size']:
                dependency.max_chunk_size = case['max_chunk_size']

            # push it
            dependency.push()

            # set aside original file copy
            original_file = os.path.join(self.temp_dir, new_file + '.orig')
            shutil.move(local_file, original_file)
            self.assertTrue(not os.path.isfile(local_file))
            self.assertTrue(os.path.isfile(original_file))

            sleep(10) # github has a delay for reliably reporting new file name/sizes

            # pull it
            dependency.pull()

            # compare original and downloaded copy
            self._compare_two_files(local_file, original_file)

            # delete local and remote copies
            for file in [local_file, original_file]:
                os.remove(file)
                self.assertTrue(not os.path.isfile(file))

            dependency.delete()
            self.assertRaises(IOError, dependency.pull)

    def test_split(self):
        """
        Verifies that the _split() method will create the proper number of chunks.
        :return:
        """
        new_file = str(randint(0, 1000000000))
        temp_filename = os.path.join(self.temp_dir, new_file)
        case = self.test_case['multi_part']
        with open(temp_filename, 'w') as file:
            file.write(case['data'])

        dependency = GitHubFile(source_filename=temp_filename)
        dependency.max_chunk_size = case['max_chunk_size']
        dependency._split()
        self.assertEqual(len(dependency.chunks), 3)
        self.assertEqual(dependency.chunks[-1], 'yz')

    def test_get_legacy_file(self):
        """
        This verifies that a file without the .123456-type extension can be accessed/downloaded.
        :return:
        """
        downloaded_legacy_file = os.path.join(self.temp_dir, os.path.basename(self.legacy_file))
        dependency = GitHubFile(source_filename=downloaded_legacy_file)
        dependency.pull()

        self._compare_two_files(self.legacy_file, downloaded_legacy_file)

    def _compare_two_files(self, file1, file2):
        """
        Helper method that compares two files for existence and data exactness
        :return:
        """
        file_data = []
        for filename in [file1, file2]:
            self.assertTrue(os.path.isfile(filename))
            with open(filename, 'rb') as file:
                file_data.append(file.read())
        self.assertEqual(file_data[0], file_data[1])

if __name__ == '__main__':
    unittest.main()
