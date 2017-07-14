from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from simtools.AssetManager.AssetCollection import AssetCollection
from simtools.AssetManager.FileList import FileList
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser
from simtools.Utilities.COMPSUtilities import get_asset_collection

if __name__ == "__main__":
    # Initialize an HPC setup
    SetupParser.init('HPC')

    # Create a FileList, this will contain all the files we want to add to the collection
    fl = FileList()

    # Lets add the custom_collection folder and have it recursively browsed
    # If recursive is False, only the file present in the directory will be added.
    # With recursive enabled, the sub directory are also scanned for files and added to the list.
    fl.add_path('inputs/custom_collection', recursive=True)

    # Create an asset collection and pass this file list
    ac = AssetCollection(local_files=fl)

    # Prepare the collection
    # This will create the collection in COMPS and send the missing files
    ac.prepare('HPC')

    # Our collection is created -> the id is:
    print("The collection ID is: %s " % ac.collection_id)

    # Now create another collection based on the one we just created and add some arbitrary files
    # First we need to create the filelist of Local files to use
    local_fl = FileList()
    local_fl.add_file('inputs/docs/some_doc.txt')

    # THen lets create an AssetCollection but this time we will give set the base_collection to be the one we created earlier
    # base_collection needs a COMPSAssetCollection instance so we can retrieve this by doing:
    comps_collection = get_asset_collection(ac.collection_id)
    new_collection = AssetCollection(base_collection=comps_collection, local_files=local_fl)

    # Dont forget to prepare the collection to send everything to COMPS
    new_collection.prepare('HPC')

    print("The new collection ID is: %s" % new_collection.collection_id)

    # Run a simulation with this new collection ID
    cb = DTKConfigBuilder.from_defaults('VECTOR_SIM')
    cb.set_param("Demographics_Filenames", ['inputs/birth_cohort_demographics.json'])
    cb.set_param("Climate_Model", "CLIMATE_CONSTANT")

    # This is where we set the collection ID used to be the one we just created
    cb.set_collection_id(new_collection.collection_id)

    # Create an experiment manager and run the simulations
    exp_manager = ExperimentManagerFactory.from_cb(cb)
    exp_manager.run_simulations(exp_name="Experiment with custom collection")

