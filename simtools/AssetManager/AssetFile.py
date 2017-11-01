import os

from simtools.Utilities.General import get_md5


class AssetFile:
    cache = {}

    def __init__(self, file_name, relative_path='', absolute_path=None):
        if not os.path.exists(absolute_path):
            raise Exception("File: %s does not exist!" % absolute_path)

        self.relative_path = os.path.normpath(relative_path)
        # Follow COMPS convention None means root
        self.relative_path = None if self.relative_path == '.' else self.relative_path
        self.file_name = os.path.normpath(file_name)

        self.absolute_path = absolute_path or os.path.join(os.getcwd(), self.relative_path, file_name)
        self.is_local = False

    @property
    def md5(self):
        if self.absolute_path not in AssetFile.cache:
            AssetFile.cache[self.absolute_path] = get_md5(self.absolute_path)

        return AssetFile.cache[self.absolute_path]

    @classmethod
    def split_path(cls, file_path):
        """
        Cannonical method for splitting a file path into relative/absolute values for creating an AssetFile object.
        :param file_path: a relative file path
        :return: a 2-tuple containing (relative_path, file_name)
        """
        relative_path, file_name = os.path.split(file_path)
        return (relative_path, file_name)
