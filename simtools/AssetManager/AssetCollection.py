import hashlib
import json
import os

from COMPS.Data.AssetCollection import AssetCollection as COMPSAssetCollection
from COMPS.Data.AssetCollectionFile import AssetCollectionFile as COMPSAssetCollectionFile


class AssetCollection(object):
    """
    This class represents a single collection of files (AssetFile) in a simulation. An object of this class is
    not usable UNLESS self.collection_id is not None
    """
    comps_collection_cache = {}
    class InvalidConfiguration(Exception): pass

    def __init__(self, base_collection=None, local_files=None, remote_files=None):
        """
        :param base_collection: A string COMPS AssetCollection id (if not None)
        :param local_files: a FileList object representing local files to use (if not None)
        :param remote_files: a COMPSAssetCollectionFile object list representing (existing) remote files to use.
        """
        if not (base_collection or local_files or remote_files):
            raise self.InvalidConfiguration("Must provide at least one of: base_collection_id, local_files, remote_files .")

        if base_collection and remote_files:
            raise self.InvalidConfiguration("May only provide one of: base_collection, remote_files")

        self.base_collection = base_collection
        self._remote_files = remote_files
        self.local_files = local_files
        self.asset_files_to_use = self._determine_files_to_use()
        self.collection_id = None
        self.comps_collection = None
        self.prepared = False # not allowed to run simulations with this collection until True (set by prepare())

    def __contains__(self, item):
        if not self.asset_files_to_use: return False
        from simtools.AssetManager.AssetFile import AssetFile
        for asset_file in self.asset_files_to_use:
            if isinstance(item, AssetFile):
                if asset_file.file_name == item.file_name: return True
            elif isinstance(item, str) or isinstance(item, unicode):
                if asset_file.file_name == item: return True
        return False

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
            self.comps_collection = self._get_or_create_collection()
            # we have no _collection if no files were added to this collection-to-be (e.g. empty dll AssetCollection)
            self.collection_id = self.comps_collection.id if self.comps_collection else None
        else: # 'LOCAL'
            self.comps_collection = None
            self.collection_id = location
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
        for asset_file in existing:
            selected[os.path.join(asset_file.relative_path or '', asset_file.file_name)] = asset_file

        for asset_file in local:
            selected[os.path.join(asset_file.relative_path or '', asset_file.file_name)] = asset_file

        return selected.values()

    def _determine_files_to_use(self):
        if not (self.base_collection or self.local_files or self._remote_files):
            raise self.InvalidConfiguration("Must provide at least one of: base_collection_id, local_files, remote_files .")

        if self.base_collection and self._remote_files:
            raise self.InvalidConfiguration("May only provide one of: base_collection_id, remote_files")

        # identify the file sources to choose from
        local_asset_files = []
        existing_asset_files = []

        if self.base_collection:
            existing_asset_files = self.base_collection.assets

        elif self._remote_files:
            existing_asset_files = self._remote_files

        if self.local_files:
            local_asset_files = []
            for asset_file in self.local_files:
                comps_file = COMPSAssetCollectionFile(file_name=asset_file.file_name,
                                                      relative_path=asset_file.relative_path,
                                                      md5_checksum=asset_file.md5)
                # Enrich it with some info
                comps_file.absolute_path = asset_file.absolute_path
                comps_file.is_local = True
                local_asset_files.append(comps_file)

        for asset_file in existing_asset_files:
            asset_file.is_local = False

        return self._merge_local_and_existing_files(local_asset_files, existing_asset_files)

    def _get_or_create_collection(self, missing=None):
        # If there are no files for this collection, so we don't do anything
        if len(self.asset_files_to_use) == 0: return None

        # Create a COMPS collection
        collection = COMPSAssetCollection()
        for af in self.asset_files_to_use:
            if not missing or af.md5_checksum not in missing:
                collection.add_asset(af)
            else:
                collection.add_asset(af, file_path=af.absolute_path)

        # Calculate MD5 of the collection
        collection_md5 = hashlib.md5(json.dumps(json.loads(str(collection)), sort_keys=True)).hexdigest()

        # The collection was already there -> returns it
        if collection_md5 in AssetCollection.comps_collection_cache:
            return AssetCollection.comps_collection_cache[collection_md5]

        # Get the missing files (if any)
        missing = collection.save(return_missing_files=True)

        # No files were missing -> we have our collection
        if not missing:
            # Add to the cache
            AssetCollection.comps_collection_cache[collection_md5] = collection

            # Return
            return collection

        # There was missing files, call again
        return self._get_or_create_collection(missing)

