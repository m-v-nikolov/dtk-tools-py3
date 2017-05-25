import os

from simtools.AssetManager.AssetCollection import AssetCollection
from simtools.AssetManager.FileList import FileList
from simtools.SetupParser import SetupParser

class SimulationAssets(object):
    """
    This class represents a set of AssetCollection objects that together define all files needed by a simulation
    that are known a priori.
    """

    class InvalidCollection(Exception): pass
    class AmbiguousAssetSpecification(Exception): pass

    EXE = 'exe'
    DLL = 'dll'
    INPUT = 'input'
    COLLECTION_TYPES = [EXE, DLL, INPUT]

    def __init__(self, collections=None):
        """

        :param collections: a dict of the known collections types needed by simulations
        """
        collections = {self.EXE: None, self.DLL: None, self.INPUT: None} if collections is None else collections
        for collection_type in self.COLLECTION_TYPES:
            collection = collections.get(collection_type, None)
            if collection is None or not isinstance(collection, AssetCollection):
                raise self.InvalidCollection("Invalid %s collection." % collection_type)
        self.collections = collections

    def prepare(self):
        """
        Calls prepare() on all unprepared contained AssetCollection objects.
        :return: Nothing
        """
        for collection in self.collections.values():
            if not collection.prepared:
                collection.prepare()

    @property
    def prepared(self):
        return not any(not c.prepared for c in self.collections.values())

    # @classmethod
    # def assemble_assets(cls, config_builder,
    #                     base_executable_id=None, base_dll_id=None, base_input_id=None,
    #                     local_executable=None, local_dll=None, local_input=None):
    @classmethod
    def assemble_assets(cls, config_builder, base_collection_id={}, use_local_files={}):
        """
        The entry point for creating a full SimulationAssets object in one go.
        :param config_builder: A DTKConfigBuilder associated with this process.
        :param base_collection_id: a dict containing keys: cls.COLLECTION_TYPES, values: None or a starting point
                                   AssetCollection id
        :param use_local_files: A dict containing keys: cls.COLLECTION_TYPES, values: True/False
        :return: A SimulationAssets object corresponding to the inputs
        """

        for collection_type in cls.COLLECTION_TYPES:
            if not (base_collection_id.get(collection_type, None) or use_local_files.get(collection_type, None)):
                raise cls.AmbiguousAssetSpecification("Must specify a base %s asset collection id and/or local file use."
                                                      % collection_type)

        collections = {}
        for collection_type in cls.COLLECTION_TYPES:
            if use_local_files[collection_type]:
                files = cls._gather_files(config_builder, collection_type)
            else:
                files = None
            collections[collection_type] = AssetCollection(base_collection_id=base_collection_id[collection_type],
                                                           local_files=files)


#        executable_collection = AssetCollection(base_collection_id=base_executable_id, local_files=files[cls.EXE])
#        dll_collection        = AssetCollection(base_collection_id=base_dll_id,        local_files=files[cls.DLL])
#        input_collection      = AssetCollection(base_collection_id=base_input_id,      local_files=files[cls.INPUT])
        return cls(collections)
        #executable_collection=executable_collection,
        #           dll_collection=dll_collection,
        #           input_collection=input_collection)

    # ck4, this needs some by-hand testing to verify it's still on track compared to the asset_manager_test.py script
    @classmethod
    def _gather_files(cls, config_builder, collection_type):
        """
        Identifies local files associated with the given collection_type.
        :param config_builder: A DTKConfigBuilder object associated with this process
        :param collection_type: one of cls.COLLECTION_TYPES
        :return: A FileList objecr
        """
        if collection_type == cls.EXE:
            exe_path = SetupParser.get('exe_path')
            file_list = FileList(root=os.path.dirname(exe_path), files_in_root=[os.path.basename(exe_path)])
        elif collection_type == cls.DLL:
            # returns a Hash with some items that need filtering through
            input_files = config_builder.get_input_file_paths()

            # remove files we will not be putting into the inputs collection
            ignored_keys = ['Campaign_Filename', 'Demographics_Filenames']
            for key in ignored_keys:
                if input_files.get(key, None):
                    input_files.pop(key)

            # remove blank filenames
            for key in input_files.keys():
                if not input_files[key]:  # None or "" values ignored
                    input_files.pop(key)
            input_files = input_files.values()

            # Also include the .bin.json file pair for each .bin file
            for file in input_files:
                base_filename, extension = os.path.splitext(file)
                if extension == '.bin':
                    input_files.append(file + '.json')
            input_files = list(set(input_files)) # just in case we somehow have duplicates
            file_list = FileList(root=SetupParser.get('input_root'), files_in_root=input_files)
        elif collection_type == cls.INPUT:
            dll_relative_paths = config_builder.get_dll_paths_for_asset_manager()
            file_list = FileList(root=SetupParser.get('dll_root'), files_in_root=dll_relative_paths)
        else:
            raise Exception("Unknown asset classification: %s" % collection_type)
        return file_list
