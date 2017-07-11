from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from simtools.AssetManager.AssetCollection import AssetCollection
from simtools.AssetManager.FileList import FileList
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser

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
    print("The new collection ID is: %s " % ac.collection_id)

    # Run a simulation with this new collection ID
    cb = DTKConfigBuilder.from_defaults('VECTOR_SIM')
    cb.set_param("Demographics_Filenames", ['inputs/birth_cohort_demographics.json'])
    cb.set_param("Climate_Model", "CLIMATE_CONSTANT")

    # This is where we set the collection ID used to be the one we just created
    cb.set_collection_id(ac.collection_id)

    # Create an experiment manager and run the simulations
    exp_manager = ExperimentManagerFactory.from_cb(cb)
    exp_manager.run_simulations(exp_name="Experiment with custom collection")

