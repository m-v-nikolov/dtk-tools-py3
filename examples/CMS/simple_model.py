from models.cms.analyzers.SimpleCMSAnalyzer import SimpleCMSAnalyzer
from models.cms.core.CMSConfigBuilder import CMSConfigBuilder
from simtools.AnalyzeManager.AnalyzeManager import AnalyzeManager
from simtools.AssetManager.SimulationAssets import SimulationAssets
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser

cb = CMSConfigBuilder.from_files(model_file='inputs/models/simplemodel.emodl',
                                 config_file='inputs/models/simplemodel.cfg')

# If the base collection containing CMS exists, use it
# If not, use the local
try:
    cb.set_collection_id('fcbbeced-ff8c-e711-9401-f0921c16849d')
except SimulationAssets.InvalidCollection:
    cb.set_experiment_executable('inputs/compartments/compartments.exe')
    cb.set_dll_root('inputs/compartments')


if __name__ == "__main__":
    SetupParser.init('HPC')
    em = ExperimentManagerFactory.from_cb(cb)
    em.run_simulations(exp_name="First CMS run")

    # Wait for the simulation to complete
    em.wait_for_finished(verbose=True)

    # Analyze
    am = AnalyzeManager(exp_list='latest')
    am.add_analyzer(SimpleCMSAnalyzer())
    am.analyze()

