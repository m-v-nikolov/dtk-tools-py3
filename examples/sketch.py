"""
This initial sketch of code handling the flow of asset/file upload to COMPS assumes we will want our simulation dir
files to have the exact same name as they are locally AND the same simulation dir rel_path. This may or may not be the
case, e.g., we may have myFavorite.exe locally, but we want it called Eradication.exe in the simulation directory. This
could be the case for all other files. It also assumes tha the AssetManage client can be queried for the basic AssetFile
information in a given AssetCollection (queried by id). This information includes: name (in sim dir), rel_path (put
'name' in SIMDIR/Assets/rel_path/ , and md5 of the file.

"""

# my_experiment.py

# some of these may not be needed after further design using AssetManager
rom dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.vector.study_sites import configure_site
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser

# Pick a collection id as the configuration starting point OR None if no starting point is desired
asset_collection_id = XYZ
load_local = True # True/False: load simtools.ini lib_staging_root and bin_staging_root
assets = Assets(collection_id=asset_collection_id, load_local=load_local)

run_sim_args = {
    'config_builder': cb,
    'exp_name': 'ExampleSim',
    'collection_id': assets.collection_id
}

if __name__ == "__main__":
    exp_manager = ExperimentManagerFactory.from_setup()
    exp_manager.run_simulations(**run_sim_args)


###########################################################################
#Assets.py

# Note: AssetManager is a stand-in for the python AssetManager interface from Jeff S.

class Assets(object):
    def __init__(self, collection_id=None, load_local=False):
        self.base_collection_id = collection_id # the initial id.
        self.collection_id = None # will be set by prepare()
        self.load_local = load_local
        self.prepare()

    def prepare(self):
        if not (self.base_collection_id or load_local):
            raise Exception("Must provide an AssetCollection id and/or specify to use local files.")

        # identify the file sources to choose from
        if self.base_collection_id:
            # obtain info for all files in the existing collection.
            existing_asset_files = AssetManager.get_asset_files(self.base_collection_id)
        if load_local:
            local_files = get_local_filenames() # via the current standard route
            local_asset_files = [AssetFile.new(local_file) for local_file in local_files]

        if self.base_collection_id and load_local:
            self.asset_files_to_use = self.merge_local_and_existing_files(local_asset_files, existing_asset_files)
        elif self.base_collection_id:
            self.asset_files_to_use = existing_asset_files
        elif load_local:
            self.asset_files_to_use = local_asset_files

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
            selected[file.sim_rel_filename] = file
        for file in local:
            selected[file.sim_rel_filename] = file
        return selected.values()

###########################################################################
# AssetFile.py

import  hashlib
import os

class AssetFile(object):
    def __init__(self, filename):
        self.filename = filename # local filename
        self.name = os.path.basename(filename) # the name of the file in the simulation dir
        # the dir inside of SIMROOT/Assets/ that self.name file will appear. May need logic to send different files
        # to different folders.
        self.rel_path = 'lib'
        self.sim_rel_filename = os.path.join(self.rel_path, self.name) # relative filename in the simulation directory
        self.checksum = hashlib.md5(open(self.filename, 'rb').read()).digest() # from stackoverflow :)
