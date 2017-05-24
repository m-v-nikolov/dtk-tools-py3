import os

from simtools.AssetManager.FileList import FileList

from COMPS.Data.AssetCollection import AssetCollection as COMPSAssetCollection
from COMPS.Data.AssetCollectionFile import AssetCollectionFile as COMPSAssetCollectionFile
from COMPS.Data.QueryCriteria import QueryCriteria as COMPSQueryCriteria

class AssetCollection(object):
    """
    This class represents a single collection of files (AssetFile) in a simulation. An object of this class is
    not usable UNLESS self.collection_id is not None
    """

    class InvalidCollectionType(Exception): pass

    class MissingFile(Exception): pass

    def __init__(self, base_collection_id = None, local_files = None):
        """
        :param base_collection_id: A string COMPS AssetCollection id (if not None)
        :param local_files: a FileList object representing local files to use (if not None)
        """
        if not (base_collection_id or local_files):
            raise Exception("Must provide a collection_id and/or a directory of asset files.")
        self.base_collection_id = base_collection_id

        if not len(local_files.invalid_files) == 0:
            raise self.MissingFile("Local file(s) slated for use are missing: %s" % local_files.invalid_files)
        self.local_files = local_files

        self.collection_id = None
        self.prepared = False # not allowed to run simulations with this collection until True (set by prepare())

    @property
    def load_local(self):
        """
        :return: True/False, should local files be used for this AssetCollection?
        """
        return not self.local_files is None

    def prepare(self):
        """
        This method handles the validation/update/synchronization of the provided collection_id and/or
        local files.
        - If only a collection id is defined, it will be used.
        - If only a load_local is set, files will be uploaded as needed and a collection id
            will be obtained from COMPS.
        - If a collection id and load_local have been defined, any files in the local system (typical discovery) that
            differ from matching files in the collection_id (or are not in collection_id) will be uploaded and
            an updated collection_id will be obtained from COMPS.
        Sets the instance flag 'prepared', which is required for running simulations with this AssetCollection.
        :return: Nothing
        """
        if self.prepared:
            return

        if not (self.base_collection_id or self.load_local):
            raise Exception("Must provide an AssetCollection id and/or specify to use local files.")

        # identify the file sources to choose from
        local_asset_files = []
        existing_asset_files = []
        if self.base_collection_id:
            # obtain info for all files in the existing collection.
            q = COMPSQueryCriteria().select_children(children=['assets'])
            existing_asset_files = COMPSAssetCollection.get(id=self.base_collection_id, query_criteria=q)
        if self.load_local:
            # via the current standard route , ck4 define/fix. local_dir should be the path that is equivalent to
            # <simdir>/Assets and local_filenames is a list of filepaths relative to <simdir>/Assets
            # (e.g. return: "/a/b/c" and ["g/h/i.json", ...] where local full path is : /a/b/c/g/h/i.json and sim path is: <simdir>/Assets/g/h/i.json
            local_asset_files = []
            for file in self.local_files.files:
                # passing name of file (no path, file_name) and full path of file (relative_path)
#                print "My AssetCollection: adding COMPSAssetCollectionFile: %s %s" % \
#                    (os.path.basename(file), os.path.join(self.local_files.root, file))
                local_asset_files.append(COMPSAssetCollectionFile(file_name=os.path.basename(file),
                                                                  relative_path=file))
        self.asset_files_to_use = self._merge_local_and_existing_files(local_asset_files, existing_asset_files)

        # interface with AssetManager to obtain an existing matching or a new asset collection id
        # Any necessary uploads of files based on checksums happens here, too.
        self._collection = self._get_or_create_collection(self.local_files.root)
        self.collection_id = self._collection.id
#        print "Got collection id: %s" % self.collection_id.id
        self.prepared = True

    @classmethod
    def _merge_local_and_existing_files(cls, local, existing):
        """
        Merges specified local and existing file sets, preferring local files based on (paren part of):
        <simdir>/Assets/(<rel_path>/<filename>)
        :param local: AssetFile objects representing local files
        :param existing: AssetFile objects representing files already in AssetManager
        :return: A list of COMPSAssetFile objects to use
        """
        selected = {}
        for file in existing:
            selected[os.path.join(file.relative_path, file.file_name)] = file
        for file in local:
            selected[os.path.join(file.relative_path, file.file_name)] = file
        return selected.values()

    def _get_or_create_collection(self, root_dir):
        collection = COMPSAssetCollection()
        for af in self.asset_files_to_use:
#            print "Adding asset filename: %s" % af.relative_path
            full_path = os.path.join(root_dir, af.relative_path)
            collection.add_asset(af, file_path=full_path)

        collection.save()
        return collection
