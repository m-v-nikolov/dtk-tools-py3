from models.cms.analyzers.SimpleCMSAnalyzer import SimpleCMSAnalyzer
from models.cms.core.CMSConfigBuilder import CMSConfigBuilder
from simtools.AnalyzeManager.AnalyzeManager import AnalyzeManager
from simtools.AssetManager.SimulationAssets import SimulationAssets
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser

SetupParser.default_block = "HPC"

# create a cb with empty config and model
cb = CMSConfigBuilder.from_defaults()

###################
# build config
###################
cb.set_config_param("duration", 365)
cb.set_config_param("runs", 1)
cb.set_config_param("samples", 365)
cb.set_config_param("solver", 'R')
cb.set_config_param("output", {"headers": True})
cb.set_config_param("tau-leaping", {"epsilon": 0.01})
cb.set_config_param("r-leaping", {})

###################
# build model
###################
# add species
cb.add_species('S', 990)
cb.add_species('E')
cb.add_species('I', 10)
cb.add_species('R')

# add observe
cb.add_observe('susceptible', 'S')
cb.add_observe('exposed', 'E')
cb.add_observe('infectious', 'I')
cb.add_observe('recovered', 'R')

# addd param
cb.add_param('Ki', 0.0005)
cb.add_param('Kl', 0.2)
cb.add_param('Kr', '(/ 1 7)')
cb.add_param('Kw', '(/ 1 135)')

# addd reaction
cb.add_reaction('exposure', '(S I)', '(E I)', '(* Ki S I)')
cb.add_reaction('infection', '(E)', '(I)', '(* Kl E)')
cb.add_reaction('recovery', '(I)', '(R)', '(* Kr I)')
cb.add_reaction('waning', '(R)', '(S)', '(* Kw R)')


########################
# other configurations
########################

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


if __name__ == "__main__":
    SetupParser.init()
    em = ExperimentManagerFactory.from_cb(cb)
    em.run_simulations(exp_name="First Default CMS run")

    # Wait for the simulation to complete
    em.wait_for_finished(verbose=True)

    # Analyze
    am = AnalyzeManager(exp_list='latest')
    am.add_analyzer(SimpleCMSAnalyzer())
    am.analyze()

