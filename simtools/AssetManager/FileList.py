import os

from simtools.AssetManager.AssetFile import AssetFile


class FileList:
    def __init__(self, root, files_in_root):
        """
        Represents a set of files that are specified RELATIVE to root.
        e.g. /a/b/c.json could be : root: '/a' files_in_root: ['b/c.json']
        :param root: The dir all files_in_root are relative to.
        :param files_in_root: The listed files
        """
        self.files = []
        for file_path in files_in_root:
            file_name = os.path.basename(file_path)
            relative_path = os.path.dirname(file_path) if len(os.path.dirname(file_path)) > 0 else ''
            absolute_path = os.path.join(root, file_path)
            self.files.append(AssetFile(file_name, relative_path, absolute_path))
        self.root = root

    @property
    def invalid_files(self):
        return [file for file in self.files if not os.path.exists(file.full_path)]

    def __iter__(self):
        return self.files.__iter__()
    
    def __getitem__(self, item):
        return self.files.__getitem__(item)

