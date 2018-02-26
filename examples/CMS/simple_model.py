from models.cms.analyzers.SimpleCMSAnalyzer import SimpleCMSAnalyzer
from models.cms.core.CMSConfigBuilder import CMSConfigBuilder
from simtools.AnalyzeManager.AnalyzeManager import AnalyzeManager
from simtools.AssetManager.SimulationAssets import SimulationAssets
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser

SetupParser.default_block = "HPC"

cb = CMSConfigBuilder.from_files(model_file='inputs/models/simplemodel.emodl',
                                 config_file='inputs/models/simplemodel.cfg')

# If the base collection containing CMS exists, use it
# If not, use the local
if SetupParser.default_block == "HPC":
    try:
        cb.set_collection_id('CMS 0.82 Pre-release')
    except SimulationAssets.InvalidCollection:
        cb.set_experiment_executable('inputs/compartments/compartments.exe')
        cb.set_dll_root('inputs/compartments')
else:
    cb.set_experiment_executable('inputs/compartments/compartments.exe')
    cb.set_dll_root('inputs/compartments')

run_sim_args = {"config_builder": cb, "exp_name": "First CMS run"}


if __name__ == "__main__":
    SetupParser.init()
    em = ExperimentManagerFactory.from_cb(run_sim_args["config_builder"])
    em.run_simulations(exp_name=run_sim_args["exp_name"])

    # Wait for the simulation to complete
    em.wait_for_finished(verbose=True)

    # Analyze
    am = AnalyzeManager(exp_list='latest')
    am.add_analyzer(SimpleCMSAnalyzer())
    am.analyze()

