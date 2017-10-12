import os

from COMPS.Data.AssetCollection import AssetCollection as COMPSAssetCollection
from simtools.AssetManager.AssetCollection import AssetCollection
from simtools.AssetManager.FileList import FileList
from simtools.SetupParser import SetupParser
from simtools.Utilities.COMPSUtilities import get_asset_collection
from simtools.Utilities.General import init_logging

logger = init_logging("SimulationAssets")


class SimulationAssets(object):
    """
    This class represents a set of AssetCollection objects that together define all files needed by a simulation.
    """
    class InvalidCollection(Exception): pass
    class NotPrepared(Exception): pass

    EXE = 'exe'
    DLL = 'dll'
    INPUT = 'input'
    LOCAL = 'local'
    MASTER = 'master'
    COLLECTION_TYPES = [DLL, EXE, INPUT]

    def __init__(self):
        self.collections = {}
        self.base_collections = {}
        self.experiment_files = FileList()
        self.prepared = False
        self.master_collection = None
        self._exe_path = None
        self._input_root = None
        self._dll_root = None

    @property
    def exe_path(self):
        return self._exe_path or SetupParser.get('exe_path')

    @exe_path.setter
    def exe_path(self, value):
        if not os.path.exists(value):
            raise Exception("The path specified in exe_path does not exist (%s)" % value)

        self.base_collections[self.EXE] = None
        self._exe_path = value

    @property
    def input_root(self):
        return self._input_root or SetupParser.get('input_root')

    @input_root.setter
    def input_root(self, input_root):
        if not os.path.exists(input_root) or not os.path.isdir(input_root):
            raise Exception(
                "The path specified in input_root does not exist or is not a directory(%s)" % input_root)

        self.base_collections[self.INPUT] = None
        self._input_root = input_root

    @property
    def dll_root(self):
        return self._dll_root or SetupParser.get('dll_root')

    @dll_root.setter
    def dll_root(self, dll_root):
        if not os.path.exists(dll_root) or not os.path.isdir(dll_root):
            raise Exception(
                "The path specified in dll_root does not exist or is not a directory(%s)" % dll_root)

        self.base_collections[self.DLL] = None
        self._dll_root = dll_root

    def __contains__(self, item):
        for col in self.collections.values():
            if item in col: return True
        return False

    @property
    def collection_id(self):
        if not self.prepared or not self.master_collection:
            raise self.NotPrepared("Cannot query asset collection id if collection is not prepared.")
        return self.master_collection.collection_id

    def set_base_collection(self, collection_type, collection):
        # Make sure we have the good inputs
        if collection_type not in self.COLLECTION_TYPES and collection_type != self.MASTER:
            raise self.InvalidCollection("Collection type %s is not supported..." % collection_type)

        if not collection:
            raise self.InvalidCollection("No collection provided in set_input_collection.")

        # If the collection given is not already an AssetCollection -> retrieve
        if not isinstance(collection, COMPSAssetCollection):
            collection_id = collection
            with SetupParser.TemporarySetup('HPC'):
                collection = get_asset_collection(collection_id)

            if not collection:
                raise self.InvalidCollection("The input collection '%s' provided could not be found on COMPS." % collection_id)

        if collection_type == self.MASTER:
            self.master_collection = AssetCollection(base_collection=collection)
        else:
            self.base_collections[collection_type] = AssetCollection(base_collection=collection)

        if collection_type == self.DLL:
            self.base_collections[self.DLL].asset_files_to_use = [a for a in self.base_collections[self.DLL].asset_files_to_use if not a.file_name.endswith('exe')]

    def prepare(self, config_builder):
        """
        Calls prepare() on all unprepared contained AssetCollection objects.
        :return: Nothing
        """
        location = SetupParser.get("type")
        self.collections = {}
        self.create_collections(config_builder)

        for collection in self.collections.values():
            if not collection.prepared:
                collection.prepare(location=location)

        # Sort the collections to first gather the assets from base collections and finish with the locally generated
        # Use a set to remove duplicates
        sorted_collections = sorted(set(self.collections.values()), key=lambda x: x.base_collection is None)

        # Gather the collection_ids from the above collections now that they have been prepared/uploaded (as needed)
        # and generate a 'super AssetCollection' containing all file references.
        asset_files = {}
        for collection in sorted_collections:
            if location == 'LOCAL':
                for asset in collection.asset_files_to_use:
                    asset_files[(asset.file_name, asset.relative_path)] = asset
            else:
                if collection.collection_id is not None: # None means "no files in this collection"
                    # Add the assets to the asset_files
                    # Make sure we have a key (file_name, path) to make sure we override assets
                    for asset in collection.comps_collection.assets:
                        asset_files[(asset.file_name, asset.relative_path)] = asset

        # Delete collections that are None (no files)
        self.collections = {cid:collection for cid, collection in self.collections.items() if collection.collection_id}

        logger.debug("Creating master collection with %d files" % len(asset_files))
        self.master_collection = AssetCollection(remote_files=asset_files.values())
        self.master_collection.prepare(location=location)
        self.prepared = True

    def create_collections(self, config_builder):
        location = SetupParser.get("type")
        for collection_type in self.COLLECTION_TYPES:
            # Dont do anything if already set
            if collection_type in self.collections and self.collections[collection_type]: continue

            # Check if we are running LOCAL we should not have any base collections
            if location == "LOCAL" and collection_type in self.base_collections:
                print("The base_collection of type %s was specified but you are trying to run a LOCAL experiment.\n"
                          "Using COMPS collection with LOCAL experiments is not supported. The collection will be ignored..." % collection_type)

            if location == "HPC":
                # If we already have the master collection set -> set it as collection for every types
                if self.master_collection:
                    self.collections[collection_type] = self.master_collection
                    continue

                if collection_type not in self.base_collections:
                    base_id = SetupParser.get('base_collection_id_%s' % collection_type, None)
                    if base_id: self.set_base_collection(collection_type, base_id)

            base_collection = self.base_collections.get(collection_type, None)
            if not base_collection:
                files = self._gather_files(config_builder, collection_type)
                if files: self.collections[collection_type] = AssetCollection(local_files=files)
            else:
                self.collections[collection_type] = base_collection

        # If there are manually added files -> add them now
        if self.experiment_files:
            self.collections[self.LOCAL] = AssetCollection(local_files=self.experiment_files)

    def _gather_files(self, config_builder, collection_type):
        """
        Identifies local files associated with the given collection_type.
        :param config_builder: A ConfigBuilder object associated with this process
        :param collection_type: one of cls.COLLECTION_TYPES
        :return: A FileList object
        """
        file_list = None
        if collection_type == self.EXE:
            exe_path = self.exe_path
            file_list = FileList(root=os.path.dirname(exe_path),
                                 files_in_root=[os.path.basename(exe_path)],
                                 ignore_missing=config_builder.ignore_missing)
        elif collection_type == self.INPUT:
            # returns a Hash with some items that need filtering through
            input_files = config_builder.get_input_file_paths()
            if input_files:
                file_list = FileList(root=self.input_root,
                                     files_in_root=input_files,
                                     ignore_missing=config_builder.ignore_missing)
        elif collection_type == self.DLL:
            dll_relative_paths = config_builder.get_dll_paths_for_asset_manager()
            if dll_relative_paths:
                file_list = FileList(root=self.dll_root,
                                     files_in_root=dll_relative_paths,
                                     ignore_missing=config_builder.ignore_missing)
        else:
            raise Exception("Unknown asset classification: %s" % collection_type)
        return file_list
