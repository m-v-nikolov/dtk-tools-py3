from simtools.AssetManager.AssetCollection import AssetCollection
from simtools.AssetManager.FileList import FileList

class SimulationAssets(object):
    """
    This class represents a set of AssetCollection objects that together define all files needed by a simulation
    that are known a priori.
    """

    class InvalidCollection(Exception): pass
    class AmbiguousAssetSpecification(Exception): pass

    def __init__(self, executable_collection, dll_collection, input_collection):
        self.collections = {
            'executable': executable_collection,
            'dll': dll_collection,
            'input': input_collection
        }
        for name, collection in self.collections.iteritems():
            if not isinstance(collection, AssetCollection):
                raise self.InvalidCollection("Invalid %s collection." % name)

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

    @classmethod
    def assemble_assets(cls, config_builder,
                        base_executable_id=None, base_dll_id=None, base_input_id=None,
                        local_executable=None, local_dll=None, local_input=None):
        """
        The entry point for creating a full SimulationAssets object in one go. # ck4, finish comments
        :param base_executable_id:
        :param base_dll_id:
        :param base_input_id:
        :param local_path:
        :return: A SimulationAssets object
        """
        # ck4, remake the above documentation

        if not (base_executable_id or local_executable):
            raise cls.AmbiguousAssetSpecification("Must specify a base executable asset collection id and/or local file use.")
        if not (base_dll_id or local_dll):
            raise cls.AmbiguousAssetSpecification("Must specify a base dll asset collection id and/or local file use.")
        if not (base_input_id or local_input):
            raise cls.AmbiguousAssetSpecification("Must specify a base input asset collection id and/or local file use.")

        executable_root = None # ck4, fix
        executable_files = FileList(root=file_root, files_in_root=cls._gather_files(config_builder, 'executable'))

        dll_root = None  # ck4, fix
        dll_files = FileList(root=file_root, files_in_root=cls._gather_files(config_builder, 'dll'))

        input_root = None  # ck4, fix
        input_files = FileList(root=file_root, files_in_root=cls._gather_files(config_builder, 'input'))

        executable_collection = AssetCollection(base_collection_id=base_executable_id, local_files=executable_files)
        dll_collection        = AssetCollection(base_collection_id=base_dll_id, local_files=dll_files)
        input_collection      = AssetCollection(base_collection_id=base_input_id, local_files=input_files)
        return cls(executable_collection=executable_collection,
                   dll_collection=dll_collection,
                   input_collection=input_collection)

    @classmethod
    def _gather_files(cls, config_builder, file_type):
        if file_type == 'executable':
            raise Exception("unimplemented")  # ck4, see asset_manager_test.py
        elif file_type == 'dll':
            raise Exception("unimplemented")  # ck4, see asset_manager_test.py
        # use config_builder.get_dll_paths_for_asset_manager
        elif file_type == 'input':
            raise Exception("unimplemented")  # ck4, see asset_manager_test.py
        else:
            raise Exception("Unknown asset classification: %s" % file_type)

