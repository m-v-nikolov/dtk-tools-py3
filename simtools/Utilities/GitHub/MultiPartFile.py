import os

from simtools.Utilities.GitHub.GitHub import DependencyGitHub

class MultiPartFile(object):

    MAX_CHUNK_SIZE = 1 * 2**20 # bytes
    CHUNK_DIGITS = 9 # create chunk file suffixes with this many digits

    def __init__(self, source_filename, max_chunk_size = None, chunk_digits = None):
        self.max_chunk_size = max_chunk_size or self.MAX_CHUNK_SIZE
        self.chunk_digits   = chunk_digits   or self.CHUNK_DIGITS
        self.source_filename  = os.path.abspath(source_filename)
        self.source_directory = os.path.dirname(source_filename)
        self.destination_directory = self.source_directory # same file either way!
        self.chunks = [] # assumed to be IN ORDER AT ALL TIMES
        self.is_split = False

    def _split(self):
        """
        Splits self.source_filename into file parts, setting self.chunks
        :return:
        """
        if self.is_split:
            raise Exception('Cannot re-split a split MultiPartFile')

        with open(self.source_filename, 'rb') as source_file:
            source_data = source_file.read()
        source_data_length = len(source_data)

        start_index = 0
        chunks = []
        while start_index < source_data_length:
            end_index = start_index + self.max_chunk_size
            if end_index > source_data_length:
                end_index = source_data_length
            chunks.append(source_data[start_index:end_index])
            start_index = end_index
        self.chunks = chunks
        self.is_split = True

    def _join(self):
        """
        Combines self.chunks into the original file, setting self.combination
        :return:
        """
        if not self.is_split:
            raise Exception('Cannot join file chunks that are not split.')

        self.chunks = ["".join(self.chunks)]
        self.is_split = False

    def _write(self):
        """
        Writes self.combination to file, creating its dest dir as needed
        :return:
        """
        destination_directory = os.path.abspath(self.destination_directory)
        dest_filename = self.source_filename
        if self.is_split:
            raise Exception('Cannot write a file that has not been joined.')
        if not os.path.exists(destination_directory):
            os.makedirs(destination_directory)
        with open(dest_filename, 'wb') as dest_file:
            dest_file.write(self.chunks[0])

class GitHubFile(MultiPartFile):
    MAX_CHUNK_SIZE = 100 * 2**20 # bytes
    CHUNK_DIGITS = 9 # create chunk file suffixes with this many digits

    def __init__(self, source_filename):
        super(GitHubFile, self).__init__(source_filename)
        self.github = DependencyGitHub() # will select the right repo as the default due to class naming/setup

    def pull(self):
        """
        Retrieve all file parts from the GitHub repo and reassemble them into the single file that is written to disk.
        :param destination_root: The directory to write the retrieved filename into.
        :return:
        """
        self._retrieve()
        self._join()
        self._write()

    def push(self):
        """
        Create all file parts on the GitHub repo
        :return:
        """
        if not self.is_split:
            self._split()

        chunk_filename_base = os.path.basename(self.source_filename)
        chunk_number = 0
        for chunk in self.chunks:
            chunk_filename = chunk_filename_base + self._make_chunk_suffix(chunk_number)
            if self.github.file_in_repository(filename=chunk_filename):
                raise Exception("Cannot overwrite existing files with push().")
            else:
                self.github.repository.create_file(path=chunk_filename, message='added new file %s' % chunk_filename, content=chunk) # move this into github.METHOD ?
            chunk_number += 1
        self.chunks = []
        self.is_split = False

    def delete(self):
        """
        Delete all parts from the GitHub repo. Cannot delete legacy files.
        :return:
        """
        done = False
        chunk_number = 0
        while not done:
            chunk_filename_base = os.path.basename(self.source_filename)
            chunk_filename = chunk_filename_base + self._make_chunk_suffix(chunk_number)
            if self.github.file_in_repository(filename=chunk_filename):
                file_to_delete = self.github.repository.file_contents(chunk_filename)
                file_to_delete.delete(message='deleting file: %s' % chunk_filename)
            else:
                done = True
            chunk_number += 1
        self.chunks = [] # nothing here to do anything with
        self.is_split = False

    def _retrieve(self):
        """
        Obtains all file parts corresponding to file: self.source_filename, setting self.chunks
        :return:
        """
        chunks = []

        # First, look for non-chunked version of the current file.
        non_chunked_file_name = os.path.basename(self.source_filename)
        if self.github.file_in_repository(non_chunked_file_name):
            chunks.append(self.github.get_file_data(non_chunked_file_name))
        else: # a non-chunked version of the file was not found, so look for chunks
            chunk_number = 0
            done = False
            while not done:
                remote_chunk_filename = non_chunked_file_name + self._make_chunk_suffix(chunk_number)
                chunk = self.github.get_file_data(remote_chunk_filename)
                if chunk:
                    chunks.append(chunk)
                    chunk_number += 1
                else:
                    done = True
            if chunk_number == 0:
                raise IOError('No matching file or file chunks found for: %s' % self.source_filename)
        self.chunks = chunks
        self.is_split = True

    def _make_chunk_suffix(self, number):
        """
        Makes file suffixes of a specific 0-filled length, like: .000123
        :param number: The (unique) number to stick on the end
        :return:
        """
        return ('.%' + '0%dd' % self.chunk_digits) % number



