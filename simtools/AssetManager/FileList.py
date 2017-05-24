import os

class FileList(object):

    def __init__(self, root, files_in_root):
        """
        Represents a set of files that are specified RELATIVE to root.
        e.g. /a/b/c.json could be : root: '/a' files_in_root: ['b/c.json']
        :param root: The dir all files_in_root are relative to.
        :param files_in_root: The listed files
        """
        self.root = root
        self.files = files_in_root

    @property
    def files_fullpath(self):
        return [os.path.join(self.root, file) for file in self.files]

    @property
    def invalid_files(self):
        return [ file for file in self.files_fullpath if not os.path.exists(file) ]
