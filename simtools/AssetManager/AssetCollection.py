import os

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

    def __init__(self, base_collection_id = None, local_files = None, remote_files = None):
        """
        :param base_collection_id: A string COMPS AssetCollection id (if not None)
        :param local_files: a FileList object representing local files to use (if not None)
        :param remote_files: a COMPSAssetCollectionFile object list representing (existing) remote files to use.
        """
        if not (base_collection_id or local_files or remote_files):
            raise Exception("Must provide at least one of: base_collection_id, local_files, remote_files .")
        if base_collection_id and remote_files:
            raise Exception("May only provide one of: base_collection_id, remote_files")
        self.base_collection_id = base_collection_id
        self._remote_files = remote_files

        if local_files and not len(local_files.invalid_files) == 0:
            raise self.MissingFile("Local file(s) slated for use are missing: %s" % local_files.invalid_files)
        self.local_files = local_files

        self.asset_files_to_use = self._determine_files_to_use()
        self.collection_id = None
        self.prepared = False # not allowed to run simulations with this collection until True (set by prepare())

    @property
    def load_local(self):
        """
        :return: True/False, should local files be used for this AssetCollection?
        """
        return not self.local_files is None

    def prepare(self, location):
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
        :location: 'HPC' or 'LOCAL' (usu. experiment.location)
        :return: Nothing
        """
        if self.prepared:
            return

        # interface with AssetManager to obtain an existing matching or a new asset collection id
        # Any necessary uploads of files based on checksums happens here, too.
        if location == 'HPC':
            root = self.local_files.root if self.local_files else None
            self._collection = self._get_or_create_collection(root_dir=root)
            # we have no _collection if no files were added to this collection-to-be (e.g. empty dll AssetCollection)
            self.collection_id = self._collection.id if self._collection else None
        else:
            self._collection = None
            self.collection_id = location # should only be 'LOCAL'
#        print "Got collection id: %s" % self.collection_id.id
        self.prepared = True

    @classmethod
    def _merge_local_and_existing_files(cls, local, existing):
        """
        Merges specified local and existing file sets, preferring local files based on (paren part of):
        <simdir>/Assets/(<rel_path>/<filename>)
        :param local: COMPSAssetFile objects representing local files
        :param existing: COMPSAssetFile objects representing files already in AssetManager
        :return: A list of COMPSAssetFile objects to use
        """
        selected = {}
        for file in existing:
            print("Merging existing file: %s %s" % (file.relative_path, file.file_name))
            relative_path = file.relative_path if file.relative_path is not None else ''
            selected[os.path.join(relative_path, file.file_name)] = file
        for file in local:
            print("Merging LOCAL file: *%s* *%s*, %s %s" % (file.relative_path, file.file_name, type(file.relative_path), type(file.file_name)))
            selected[os.path.join(file.relative_path, file.file_name)] = file
        print("selected files: %s" % selected)
        return selected.values()

    def _determine_files_to_use(self):
        if not (self.base_collection_id or self.load_local or self._remote_files):
            raise Exception("Must provide at least one of: base_collection_id, local_files, remote_files .")
        if self.base_collection_id and self._remote_files:
            raise Exception("May only provide one of: base_collection_id, remote_files")

        # identify the file sources to choose from
        local_asset_files = []
        existing_asset_files = []
        if self.base_collection_id:
            # obtain info for all files in the existing collection.
            existing_asset_files = COMPSAssetCollection.get(id=self.base_collection_id,
                                                            query_criteria=self.asset_files_query()) # ck4, this is not right; need to grab files off of the return, and test this case
        elif self._remote_files:
            print("Noted %d remote files" % len(self._remote_files))
            print("They are:\n%s" % self._remote_files)
            existing_asset_files = self._remote_files

        if self.load_local:
            local_asset_files = []
            for file in self.local_files.files:
                relative_path = os.path.dirname(file) if len(os.path.dirname(file)) > 0 else ''
                local_asset_files.append(COMPSAssetCollectionFile(file_name=os.path.basename(file),
                                                                  relative_path=relative_path))

        # This is necessary so that _get_or_create_collection() can determine which COMPSAssetFile objects need
        # to be discovered locally (via full path)
        for file in local_asset_files:
            file.is_local = True
            file.root = self.local_files.root
        for file in existing_asset_files:
            file.is_local = False

        return self._merge_local_and_existing_files(local_asset_files, existing_asset_files)

    def _get_or_create_collection(self, root_dir):
        if len(self.asset_files_to_use) == 0:
            return None # there are no files for this collection, so we don't do anything

        collection = COMPSAssetCollection()
        for af in self.asset_files_to_use:
            if af.is_local:
                full_path = os.path.join(root_dir, af.relative_path, af.file_name)
                print "--------------------------------------------------------------------"
                print "*** Adding asset filename FULL PATH: %s" % full_path
                print "*** *** relative path: %s" % af.relative_path
                collection.add_asset(af, file_path=full_path) # file_path here will trigger the MD5 checksum
            else:
                collection.add_asset(af)

        collection.save()
        return collection

    @staticmethod
    def asset_files_query():
        return COMPSQueryCriteria().select_children(children=['assets'])
