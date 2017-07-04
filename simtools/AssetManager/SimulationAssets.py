import os

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
    LOCAL = 'local'
    COLLECTION_TYPES = [EXE, DLL, INPUT]

    def __init__(self, collections):
        """
        :param collections: a dict of the known collections types needed by simulations
        """
        self.collections = collections
        self.master_collection = None
        self.prepared = False

    def __contains__(self, item):
        for col in self.collections.values():
            if item in col: return True
        return False

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
                    asset_files += collection.comps_collection.assets

        logger.debug("Creating master collection with %d files" % len(asset_files))
        self.master_collection = AssetCollection(remote_files=asset_files)
        self.master_collection.prepare(location=location)
        self.prepared = True

    @classmethod
    def assemble_assets(cls, config_builder, base_collections=None, experiment_files=None, cache=None):
        """
        The entry point for creating a full SimulationAssets object in one go.
        :param experiment_files: Files added by the user that need to be part of the collection
        :param base_collections: Dictionnary collection_type:comps_collection for the base collections
        :param cache: Cache to keep fullpath:md5
        :param config_builder: A DTKConfigBuilder associated with this process.
        :return: A SimulationAssets object corresponding to the inputs
        """
        base_collections = base_collections or {}

        collections = {}
        for collection_type in cls.COLLECTION_TYPES:
            base_collection = base_collections.get(collection_type, None)
            if not base_collection:
                files = cls._gather_files(config_builder, collection_type)

                if files:
                    collections[collection_type] = AssetCollection(local_files=files, cache=cache)
            else:
                collections[collection_type] = AssetCollection(base_collection=base_collection, cache=cache)

        # If there are manually added files -> add them now
        if experiment_files:
            collections[cls.LOCAL] = AssetCollection(base_collection=None, local_files=experiment_files, cache=cache)

        return cls(collections)

    @classmethod
    def _gather_files(cls, config_builder, collection_type):
        """
        Identifies local files associated with the given collection_type.
        :param config_builder: A DTKConfigBuilder object associated with this process
        :param collection_type: one of cls.COLLECTION_TYPES
        :return: A FileList object
        """
        file_list = None
        if collection_type == cls.EXE:
            exe_path = SetupParser.get('exe_path')
            file_list = FileList(root=os.path.dirname(exe_path), files_in_root=[os.path.basename(exe_path)])
        elif collection_type == cls.INPUT:
            # returns a Hash with some items that need filtering through
            input_files = config_builder.get_input_file_paths()
            if input_files:
                file_list = FileList(root=SetupParser.get('input_root'), files_in_root=input_files, recursive=True)
        elif collection_type == cls.DLL:
            dll_relative_paths = config_builder.get_dll_paths_for_asset_manager()
            if dll_relative_paths:
                file_list = FileList(root=SetupParser.get('dll_root'), files_in_root=dll_relative_paths, recursive=True)
        else:
            raise Exception("Unknown asset classification: %s" % collection_type)
        return file_list
