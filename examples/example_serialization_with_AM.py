import shutil
import os
from dtk.generic.serialization import load_Serialized_Population
from dtk.utils.analyzers.DownloadAnalyzer import DownloadAnalyzer
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from simtools.AnalyzeManager.AnalyzeManager import AnalyzeManager
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser

SetupParser.default_block = 'HPC'

cb = DTKConfigBuilder.from_defaults('VECTOR_SIM')
state_file = 'cleared-state-25550.dtk'
temp_path = 'tempdl'
source_simulation = '6ce475d8-15aa-e711-9414-f0921c16b9e5'

if __name__ == "__main__":
    # Download the state file
    da = DownloadAnalyzer(filenames=["output\\{}".format(state_file)], output_path=temp_path)
    am = AnalyzeManager(sim_list=[source_simulation], analyzers=[da])
    am.analyze()

    # Add the state file
    cb.experiment_files.add_file(os.path.join(temp_path, source_simulation, state_file))
    load_Serialized_Population(cb, 'Assets', [state_file])

    # Run !
    SetupParser.init()
    exp_manager = ExperimentManagerFactory.from_cb(cb)
    exp_manager.run_simulations(exp_name='test serialization')

    # Cleanup temp directory
    shutil.rmtree(temp_path)
