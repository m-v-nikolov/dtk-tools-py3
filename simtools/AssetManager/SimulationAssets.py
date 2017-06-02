import os

from COMPS.Data.AssetCollection import AssetCollection as COMPSAssetCollection

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

        exe_collection = collections[self.EXE]
        if exe_collection.local_files:
            self.local_executable = os.path.join(exe_collection.local_files.root,
                                                 exe_collection.asset_files_to_use[0].relative_path,
                                                 exe_collection.asset_files_to_use[0].file_name)
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
            raise Exception("Cannot query asset collection id if collection is not prepared.")
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
        for collection in self.collections.values():
            if location == 'LOCAL':
                asset_files += collection.asset_files_to_use
            else:
                print "Getting collection with id: %s" % collection.collection_id
                if collection.collection_id is not None: # None means "no files in this collection"
                    comps_collection = (COMPSAssetCollection.get(id=collection.collection_id,
                                                                 query_criteria=AssetCollection.asset_files_query()))
                    asset_files += comps_collection.assets
        print("Creating master collection with %d files" % len(asset_files))
        self.master_collection = AssetCollection(remote_files=asset_files)
        print("master collection has %d files" % len(self.master_collection.asset_files_to_use))
        self.master_collection.prepare(location=location)
        self.prepared = True
        print "-----------------------------------------\nMaster collection prepared the following:\n\n%s" % self.master_collection.asset_files_to_use

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

    # ck4, this needs some testing
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
            print("input_files: %s" % input_files)

            # remove files we will not be putting into the inputs collection
            #ignored_keys = ['Campaign_Filename', 'Demographics_Filenames']
            ignored_keys = ['Campaign_Filename']
            for key in ignored_keys:
                if input_files.get(key, None):
                    input_files.pop(key)
                print("input_files: %s" % input_files)

            # remove blank filenames
            for key in input_files.keys():
                if not input_files[key]:  # None or "" values ignored
                    input_files.pop(key)
            input_files = input_files.values()
            print("input_files: %s" % input_files)

            # flatten the list of filenames, in case there are lists in the list
            for item in input_files:
                if isinstance(item, list):
                    input_files.remove(item)
                    for i in item:
                        input_files.append(i)
            # Also include the .bin.json file pair for each .bin file
            for file in input_files:
#                print("file: %s" % file)
#                if not isinstance(file, list):
#                    files = [file]
#                else:
#                    print("FOUND LIST")
#                    files = file
#                print("FILES: %s" % files)
#                for f in files:
                base_filename, extension = os.path.splitext(file)
                if extension == '.bin':
                    input_files.append(file + '.json')
#            print input_files
#            exit()
            input_files = list(set(input_files)) # just in case we somehow have duplicates
#            print("input_files: %s" % input_files)
#            exit()
            file_list = FileList(root=SetupParser.get('input_root'), files_in_root=input_files)
        elif collection_type == cls.DLL:
            dll_relative_paths = config_builder.get_dll_paths_for_asset_manager()
            file_list = FileList(root=SetupParser.get('dll_root'), files_in_root=dll_relative_paths)
        else:
            raise Exception("Unknown asset classification: %s" % collection_type)
        return file_list
