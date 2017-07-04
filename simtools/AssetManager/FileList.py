import os

from simtools.AssetManager.AssetFile import AssetFile


class FileList:
    def __init__(self, root=None, files_in_root=None, recursive=False):
        """
        Represents a set of files that are specified RELATIVE to root.
        e.g. /a/b/c.json could be : root: '/a' files_in_root: ['b/c.json']
        :param root: The dir all files_in_root are relative to.
        :param files_in_root: The listed files
        """
        self.files = []

        if root:
            self.add_path(path=root, files_in_dir=files_in_root, recursive=recursive)

    def add_asset_file(self, af):
        self.files.append(af)

    def add_file(self, path, relative_path=''):
        absolute_path = os.path.abspath(path)
        file_name = os.path.basename(path)
        af = AssetFile(file_name, relative_path, absolute_path)
        self.add_asset_file(af)

    def add_path(self, path, files_in_dir=None, relative_path=None, recursive=False):
        if not os.path.isdir(path):
            raise RuntimeError("add_path() requires a directory. '%s' is not." % path)

        # Make sure we have an absolute path
        path = os.path.abspath(path)

        # Walk through the path
        for root, subdirs, files in os.walk(path):
            # Add the files in the current dir
            for f in files:
                # Find the file relative path compared to the root folder
                # If the relative_path is . -> change it into ''
                f_relative_path = os.path.normpath(os.path.relpath(root, path))
                if f_relative_path == '.': f_relative_path = ''

                # if files_in_dir specified -> skip the ones not included
                if files_in_dir and f not in files_in_dir and os.path.join(f_relative_path, f) not in files_in_dir: continue

                # if we want to force a relative path -> force it
                if relative_path is not None:
                    f_relative_path = relative_path

                # add the file
                self.add_file(os.path.join(root, f), relative_path=f_relative_path)

            # Stop here if we dont want to be recursive
            if not recursive: break

    @property
    def invalid_files(self):
        return [file for file in self.files if not os.path.exists(file.full_path)]

    def __iter__(self):
        return self.files.__iter__()
    
    def __getitem__(self, item):
        return self.files.__getitem__(item)

