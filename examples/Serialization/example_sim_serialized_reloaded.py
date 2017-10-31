from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.vector.study_sites import configure_site
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser
from simtools.ModBuilder import SingleSimulationBuilder
from dtk.generic import serialization
from os import path

# This block will be used unless overridden on the command-line
SetupParser.default_block = 'EXAMPLE'

cb_serializing = DTKConfigBuilder.from_defaults('VECTOR_SIM')
configure_site(cb_serializing, 'Namawala')

cb_reloading = DTKConfigBuilder.from_defaults('VECTOR_SIM')
configure_site(cb_reloading, 'Namawala')



if __name__ == "__main__":
    SetupParser.init()
    exp_manager = ExperimentManagerFactory.from_setup()

    timesteps_to_serialize = [5, 10, 50]
    old_simulation_duration = cb_serializing.params["Simulation_Duration"]
    serialized_last_timestep = timesteps_to_serialize[-1]
    serialization.add_SerializationTimesteps(config_builder=cb_serializing,
                                             timesteps=timesteps_to_serialize,
                                             end_at_final=True)

    serialized_builder = SingleSimulationBuilder()
    exp_manager.run_simulations(config_builder=cb_serializing,
                                exp_builder=serialized_builder,
                                exp_name="Sample serialization test")
    exp_manager.wait_for_finished()

    serialized_sim = exp_manager.experiment.simulations[0]
    serialized_output_path = path.join(serialized_sim.get_path(), 'output')
    s_pop_filename = "state-00050.dtk"

    reloaded_builder = SingleSimulationBuilder()
    cb_reloading.params["Start_Time"] = serialized_last_timestep
    cb_reloading.params["Simulation_Duration"] = old_simulation_duration - serialized_last_timestep
    cb_reloading.params.pop("Serialization_Time_Steps")
    serialization.load_Serialized_Population(config_builder=cb_reloading,
                                             population_filenames=[s_pop_filename],
                                             population_path=serialized_output_path,
                                             )
    exp_manager.run_simulations(config_builder=cb_reloading,
                                exp_builder=reloaded_builder,
                                exp_name="Sample serialization test")

