import os

from COMPS.Data.AssetCollection import AssetCollection as COMPSAssetCollection

from simtools.AssetManager.AssetCollection import AssetCollection
from simtools.AssetManager.FileList import FileList
from simtools.SetupParser import SetupParser
from simtools.Utilities.General import init_logging

logger = init_logging("SimulationAssets")


class SimulationAssets:
    """
    This class represents a set of AssetCollection objects that together define all files needed by a simulation
    that are known a priori.
    """

    class InvalidCollection(Exception): pass
    class AmbiguousAssetSpecification(Exception): pass
    class NotPrepared(Exception): pass

    EXE = 'exe'
    DLL = 'dll'
    INPUT = 'input'
    COLLECTION_TYPES = [EXE, DLL, INPUT]

    def __init__(self, collections):
        """
        :param collections: a dict of the known collections types needed by simulations
        """
        if not collections:
            raise Exception("SimulationAssets needs to be created with a dictionary associating collection type to the collection object. \n"
                            "Types expected %s" % ", ".join(self.COLLECTION_TYPES))

        for collection_type in self.COLLECTION_TYPES:
            collection = collections.get(collection_type, None)
            if not collection or not isinstance(collection, AssetCollection):
                raise self.InvalidCollection("Invalid %s collection." % collection_type)

        self.collections = collections

        exe_collection = collections[self.EXE]
        if exe_collection.local_files:
            self.local_executable = exe_collection.local_files[0].absolute_path
        else:
            self.local_executable = None

        input_collection = collections[self.INPUT]
        if input_collection.local_files:
            self.local_input_root = input_collection.local_files.root

        self.master_collection = None
        self.prepared = False

    @property
    def collection_id(self):
        if not self.prepared or not self.master_collection:
            raise self.NotPrepared("Cannot query asset collection id if collection is not prepared.")
        return self.master_collection.collection_id

    def prepare(self, location):
        """
        Calls prepare() on all unprepared contained AssetCollection objects.
        :location: 'HPC' or 'LOCAL' (usu. experiment.location)
        :return: Nothing
        """
        for collection in self.collections.values():
            if not collection.prepared:
                collection.prepare(location=location)

        # Gather the collection_ids from the above collections now that they have been prepared/uploaded (as needed)
        # and generate a 'super AssetCollection' containing all file references.
        asset_files = []
        for collection_type, collection in self.collections.iteritems():
            if location == 'LOCAL':
                asset_files += collection.asset_files_to_use
            else:
                logger.debug("Using %s collection with id: %s" % (collection_type, collection.collection_id))
                if collection.collection_id is not None: # None means "no files in this collection"
                    comps_collection = (COMPSAssetCollection.get(id=collection.collection_id,
                                                                 query_criteria=AssetCollection.asset_files_query()))
                    asset_files += comps_collection.assets
        logger.debug("Creating master collection with %d files" % len(asset_files))
        self.master_collection = AssetCollection(remote_files=asset_files)
        self.master_collection.prepare(location=location)
        self.prepared = True

    @classmethod
    def assemble_assets(cls, config_builder, base_collection_id=None, use_local_files=None, local_overrides=None, cache=None):
        """
        The entry point for creating a full SimulationAssets object in one go.
        :param cache: Cache to keep fullpath:md5
        :param local_overrides: Dictionarry associating colelction_type:[AssetFile()] to overrides local file to a certain collection
        :param config_builder: A DTKConfigBuilder associated with this process.
        :param base_collection_id: a dict containing keys: cls.COLLECTION_TYPES, values: None or a starting point
                                   AssetCollection id
        :param use_local_files: A dict containing keys: cls.COLLECTION_TYPES, values: True/False
        :return: A SimulationAssets object corresponding to the inputs
        """
        base_collection_id = base_collection_id or {}
        use_local_files = use_local_files or {}
        local_overrides = local_overrides or {}

        # verify all needed collection types are represented in the inputs and verify each type has been properly set
        for collection_type in cls.COLLECTION_TYPES:
            if not (base_collection_id.get(collection_type, None) or use_local_files.get(collection_type, None)):
                raise cls.AmbiguousAssetSpecification("Must specify a base %s asset collection id and/or local file use."
                                                      % collection_type)

        collections = {}
        for collection_type in cls.COLLECTION_TYPES:
            if use_local_files[collection_type]:
                files = cls._gather_files(config_builder, collection_type)
                # apply the overrides
                if collection_type in local_overrides:
                    for override in local_overrides[collection_type]:
                        files.files.append(override)
            else:
                files = None

            collections[collection_type] = AssetCollection(base_collection_id=base_collection_id[collection_type],
                                                           local_files=files, cache=cache)

        return cls(collections)

    @classmethod
    def _gather_files(cls, config_builder, collection_type):
        """
        Identifies local files associated with the given collection_type.
        :param config_builder: A DTKConfigBuilder object associated with this process
        :param collection_type: one of cls.COLLECTION_TYPES
        :return: A FileList object
        """
        if collection_type == cls.EXE:
            exe_path = SetupParser.get('exe_path')
            file_list = FileList(root=os.path.dirname(exe_path), files_in_root=[os.path.basename(exe_path)])
        elif collection_type == cls.INPUT:
            # returns a Hash with some items that need filtering through
            input_files = config_builder.get_input_file_paths()
            file_list = FileList(root=SetupParser.get('input_root'), files_in_root=input_files)
        elif collection_type == cls.DLL:
            dll_relative_paths = config_builder.get_dll_paths_for_asset_manager()
            file_list = FileList(root=SetupParser.get('dll_root'), files_in_root=dll_relative_paths)
        else:
            raise Exception("Unknown asset classification: %s" % collection_type)
        return file_list
