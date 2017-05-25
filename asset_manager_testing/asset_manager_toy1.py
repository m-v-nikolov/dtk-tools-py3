import os

from COMPS.Data.AssetCollection import AssetCollection
from COMPS.Data.AssetCollectionFile import AssetCollectionFile
from COMPS.Data.QueryCriteria import QueryCriteria
from COMPS import Client
from simtools.SetupParser import SetupParser

def COMPS_login(endpoint):
    try:
        Client.auth_manager()
    except:
        Client.login(endpoint)

sp = SetupParser('AM')
COMPS_login(sp.get('server_endpoint'))

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
