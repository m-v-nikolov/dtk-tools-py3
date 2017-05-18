from simtools.AssetManager import AssetFile

class AssetCollection(object):
    """
    This class represents a single collection of files (AssetFile) in a simulation. An object of this class is
    not usable UNLESS self.collection_id is not None
    """

    class InvalidCollectionType(Exception):
        pass

    def __init__(self, base_collection_id = None, load_local = False):
        if not (base_collection_id or load_local):
            raise Exception("Must provide a collection_id and/or a directory of asset files.")
        self.base_collection_id = base_collection_id
        self.load_local = load_local
        self.collection_id = None

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
        :return:
        """
        if not (self.base_collection_id or load_local):
            raise Exception("Must provide an AssetCollection id and/or specify to use local files.")

        # identify the file sources to choose from
        local_asset_files = []
        existing_asset_files = []
        if self.base_collection_id:
            # obtain info for all files in the existing collection.
            existing_asset_files = AssetManager.get_asset_files(self.base_collection_id)
        if self.load_local:
            local_files = get_local_filenames() # via the current standard route
            local_asset_files = [AssetFile.new(local_file) for local_file in local_files]
        self.asset_files_to_use = self.merge_local_and_existing_files(local_asset_files, existing_asset_files)

        # interface with AssetManager to obtain an existing matching or a new asset collection id
        # Any necessary uploads of files based on checksums happens here, too.
        self.collection_id = AssetManager.get_or_create_collection(self.asset_files_to_use)

    def merge_local_and_existing_files(self, local, existing):
        """
        Merges specified local and existing file sets, preferring local files
        :param local: AssetFile objects representing local files
        :param existing: AssetFile objects representing files already in AssetManager
        """
        selected = {}
        for file in existing:
            selected[file.assets_directory] = file
        for file in local:
            selected[file.assets_directory] = file
        return selected.values()