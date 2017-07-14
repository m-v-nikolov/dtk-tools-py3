def add_SerializationTimesteps(config_builder, timesteps, end_at_final=False):
    """
    Serialize the population of this simulation at specified timesteps.
    If the simulation is run on multiple cores, multiple files will be created.

    :param config_builder: A DTK Config builder
    :param timesteps: Array of integers representing the timesteps to use
    :param end_at_final: (False) set the simulation duration such that the last
                         serialized_population file ends the simluation. NOTE: may not work
                         if timestep size is not 1
    """
    config_builder.set_param("Serialization_Time_Steps", sorted(timesteps))
    if end_at_final:
        start_day = config_builder.params["Start_Time"]
        last_serialization_day = sorted(timesteps)[-1]
        end_day = start_day + last_serialization_day
        config_builder.set_param("Simulation_Duration", end_day)

def load_Serialized_Population(config_builder, population_path, population_filenames):
    """
    Sets simulation to load a serialized population from the filesystem

    :param config_builder: a DTK config builder
    :param population_path: relative path from the working directory to
                            the location of the serialized population files.
    :param population_filenames: names of files in question
    """
    config_builder.set_param("Serialized_Population_Path", population_path)
    config_builder.set_param("Serialized_Population_Filenames", population_filenames)
