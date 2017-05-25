from COMPS import Client
from simtools.SetupParser import SetupParser
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.utils.reports.CustomReport import BaseReport
from dtk.vector.study_sites import configure_site

from simtools.AssetManager.SimulationAssets import SimulationAssets

BAR = "".join(['-' for i in range(80)])

def COMPS_login(endpoint):
    try:
        Client.auth_manager()
    except:
        Client.login(endpoint)

SetupParser.init('AM')
COMPS_login(SetupParser.get('server_endpoint'))

# from example_sim.py
cb = DTKConfigBuilder.from_defaults('VECTOR_SIM')
configure_site(cb, 'Namawala')

cb.add_reports(BaseReport(type="ReportVectorStats"))
cb.add_reports(BaseReport(type="ReportVectorMigration"))
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

base_collection_id = {}
use_local_files = {}
for collection_type in SimulationAssets.COLLECTION_TYPES:
    # Each is either None (no existing collection starting point) or an asset collection id
    base_collection_id[collection_type] = SetupParser.get('base_collection_id'+'_'+collection_type)
    if len(base_collection_id[collection_type]) == 0:
        base_collection_id[collection_type] = None
    # True/False, overlay locally-discovered files on top of any provided asset collection id?
    use_local_files[collection_type] = SetupParser.getboolean('use_local' + '_' + collection_type)

print "Using base_collection_id: %s" % base_collection_id
print "Using local_files: %s" % use_local_files

# Takes care of the logic of knowing which files (remote and local) to use in coming simulations and
# creating local AssetCollection instances internally to represent them.
assets = SimulationAssets.assemble_assets(config_builder=cb,
                                          base_collection_id=base_collection_id,
                                          use_local_files=use_local_files)
assets.prepare() # This uploads any local files that need to be & records the COMPS AssetCollection ids assigned.

# now simulations can be run using the specified assets

for type, collection in assets.collections.iteritems():
    print BAR
    print "Collection type: %s" % type
    print "\n".join(collection.local_files.files)

