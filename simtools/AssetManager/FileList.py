import os

from simtools.AssetManager.AssetFile import AssetFile


class FileList:
    def __init__(self, root=None, files_in_root=None, recursive=False, ignore_missing=False):
        """
        Represents a set of files that are specified RELATIVE to root.
        e.g. /a/b/c.json could be : root: '/a' files_in_root: ['b/c.json']
        :param root: The dir all files_in_root are relative to.
        :param files_in_root: The listed files
        """
        self.files = []
        self.ignore_missing = ignore_missing

        # Make sure we have correct separator
        if files_in_root is not None:
            files_in_root = [os.path.normpath(f) for f in files_in_root]

        if root:
            self.add_path(path=root, files_in_dir=files_in_root, recursive=recursive)

    def add_asset_file(self, af):
        self.files.append(af)

    def add_file(self, path, relative_path=''):
        from simtools.Utilities.COMPSUtilities import translate_COMPS_path
        path = translate_COMPS_path(path)

        if os.path.isdir(path):
            raise ValueError("%s is a directory. add_file is expecting a file!" % path)

        absolute_path = os.path.abspath(path)
        file_name = os.path.basename(path)
        try:
            af = AssetFile(file_name, relative_path, absolute_path)
            self.add_asset_file(af)
        except Exception as e:
            if not self.ignore_missing: raise e

    def add_path(self, path, files_in_dir=None, relative_path=None, recursive=False):
        """
        Add a path to the file list.
        :param path: The path to add (needs to be a dictionary)
        :param files_in_dir: If we want to only retrieve certain files in this path
        :param relative_path: The relative path prefixed to each added files
        :param recursive: Do we want to browse recursively
        """
        from simtools.Utilities.COMPSUtilities import translate_COMPS_path
        path = os.path.abspath(translate_COMPS_path(path))
        
        # Little safety
        if not os.path.isdir(path) and not path.startswith('\\\\'):
            raise RuntimeError("add_path() requires a directory. '%s' is not." % path)

        if not recursive:
            if files_in_dir is None:
                files_in_dir = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

            for file_name in files_in_dir:
                file_path = os.path.join(path, file_name)
                f_relative_path = os.path.normpath(file_path.replace(path+"\\", '').replace(os.path.basename(file_path), ''))
                if relative_path is not None:
                    f_relative_path = os.path.join(relative_path, f_relative_path)
                self.add_file(file_path, relative_path=f_relative_path)

        else:
            # Limit the max_depth just in case
            max_depth = 3

            # Walk through the path
            for root, subdirs, files in os.walk(path):
                # Little safety to not go too deep
                depth = root[len(path) + len(os.path.sep):].count(os.path.sep)
                if depth > max_depth: continue

                # Add the files in the current dir
                for f in files:
                    # Find the file relative path compared to the root folder
                    # If the relative_path is . -> change it into ''
                    f_relative_path = os.path.normpath(os.path.relpath(root, path))
                    if f_relative_path == '.': f_relative_path = ''

                    # if files_in_dir specified -> skip the ones not included
                    if files_in_dir is not None and f not in files_in_dir and os.path.join(f_relative_path, f) not in files_in_dir: continue

                    # if we want to force a relative path -> force it
                    if relative_path is not None:
                        f_relative_path = os.path.join(relative_path, f_relative_path)

                    # add the file
                    self.add_file(os.path.join(root, f), relative_path=f_relative_path)

    def __iter__(self):
        return self.files.__iter__()
    
    def __getitem__(self, item):
        return self.files.__getitem__(item)

