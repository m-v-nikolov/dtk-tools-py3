import os

from COMPS import Client
from simtools.SetupParser import SetupParser
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.vector.study_sites import configure_site

from simtools.AssetManager.FileList import FileList
from simtools.AssetManager.AssetCollection import AssetCollection
from simtools.AssetManager.SimulationAssets import SimulationAssets
from dtk.utils.reports.CustomReport import BaseReport

BAR = "".join(['-' for i in range(80)])

def COMPS_login(endpoint):
    try:
        Client.auth_manager()
    except:
        Client.login(endpoint)

sp = SetupParser('AM')
COMPS_login(sp.get('server_endpoint'))

# from example_sim.py
cb = DTKConfigBuilder.from_defaults('VECTOR_SIM')
configure_site(cb, 'Namawala')

cb.add_reports(BaseReport(type="ReportVectorStats"))
cb.add_reports(BaseReport(type="ReportVectorMigration"))
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# ck4, move this logic into collection-type-specific methods/classes. Don't keep it here at the experiment level.

#
# EXE COLLECTION
#

# ck4, hints this block

#[DEFAULT]
#max_threads = 16
#exe_path = C:\Eradication\malariaongoing\Eradication.exe


#self.model_file = model_file or sp.get('exe_path')
#self.staged_bin_path = self.config_builder.stage_executable(self.model_file, sp.get('bin_staging_root'))

exe_path = sp.get('exe_path')
exe_list = FileList(os.path.dirname(exe_path), [os.path.basename(exe_path)])
print "Including exe file: %s" % exe_path

exe_collection = AssetCollection(base_collection_id=None, local_files=exe_list)
exe_collection.prepare()

print "EXE asset collection id: %s" % exe_collection.collection_id
print "Asset files in exe collection to use: %s" % exe_collection.asset_files_to_use
print
print BAR
print

#
# DLL COLLECTION
#

# ck4, make sure this is AFTER all reporters/other dll sources are added in the experiment code
dll_relative_paths = cb.get_dll_paths_for_asset_manager()
dll_root = sp.get('dll_path')
print "Including %d dll files:\n%s" % (len(dll_relative_paths), "\n".join(dll_relative_paths))

dll_list = FileList(dll_root, dll_relative_paths)

dll_collection = AssetCollection(base_collection_id=None, local_files=dll_list)
dll_collection.prepare()
print "DLL asset collection id: %s" % dll_collection.collection_id
print "Asset files in dll collection to use: %s" % dll_collection.asset_files_to_use
print
print BAR
print

#
# INPUTS COLLECTION
#

input_files = cb.get_input_file_paths() # returns a Hash with some items that need filtering through

# remove files we will not be putting into the inputs collection
ignored_keys = ['Campaign_Filename', 'Demographics_Filenames']
for key in ignored_keys:
    if input_files.get(key, None):
        input_files.pop(key)

# remove blank filenames
for key in input_files.keys():
    if not input_files[key]: # None or "" values ignored
        input_files.pop(key)
input_files = input_files.values()

# now for the remainder if it is a .bin file, also include the .bin.json file
for file in input_files:
    base_filename, extension = os.path.splitext(file)
    if extension == '.bin':
        input_files.append(file+'.json')
list = FileList(sp.get('input_root'), input_files)

# ck4, end
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

input_collection = AssetCollection(base_collection_id=None, local_files=list)
input_collection.prepare()
print "Input asset collection id: %s" % input_collection.collection_id
print "Asset files in inputs collection to use: %s" % input_collection.asset_files_to_use
print
print BAR
print

exit()


#############################################################






rel_path = 'asset_samples'

def create_or_retrieve_asset_collection():
    # sample for creating a collection
    collection = AssetCollection()
    dir = os.path.join(os.getcwd(), rel_path)
    files = os.listdir(dir)
    for file in files:
        rel_path_file = os.path.join(dir, file)
        print "adding file to collection: rel_path: %s file: %s" % (rel_path_file, file)
        asset_file = AssetCollectionFile(file_name=file, relative_path=rel_path)
        #print "file relative path: %s file_name: %s" % (asset_file.relative_path, asset_file.file_name)
        collection.add_asset(asset_file, file_path=rel_path_file)
    collection.save()
    return collection

# create a collection
f = os.path.join(rel_path, 'file1')
with open(f, mode='a') as file:
    file.write('a')
file.close()

collection = create_or_retrieve_asset_collection()
print "Collection id for these files: %s" % (collection.id)
#print "the collection has %d assets." % len(collection.assets)

# modify it and see the different collection id
f = os.path.join(rel_path, 'file1')
with open(f, mode='a') as file:
    file.write('a')

prior_collection = collection
collection = create_or_retrieve_asset_collection()
print "Collection id for these files: %s same? %s (expected False)" % (collection.id, collection.id == prior_collection.id)
#print "the collection has %d assets." % len(collection.assets)

# do it a third time with no changes to see the collection id is unchanged

prior_collection = collection
collection = create_or_retrieve_asset_collection()
print "Collection id for these files: %s same? %s (expected True)" % (collection.id, collection.id == prior_collection.id)
#print "the collection has %d assets." % len(collection.assets)



# sample for retrieving the files (assets) of a collection
q = QueryCriteria().select_children(children=['assets'])

result = AssetCollection.get(id=collection.id, query_criteria=q)
print result
