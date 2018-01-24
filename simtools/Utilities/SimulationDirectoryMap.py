import os


class SimulationDirectoryMap:
    """
    This class allows to keep a Simulation directory map globally.
    """
    dir_map = {}

    @staticmethod
    def get_simulation_path(simulation, save_dir_map=True):
        """
        Get the simulation path for a given simulation.
        Will first try to get it from the cache or directly from the object if not present.
        :param simulation: The simulation we want the path
        :param save_dir_map: If we do not find the simulation in the cache. Should we generate the map?
        """
        if simulation.id in SimulationDirectoryMap.dir_map:
            return SimulationDirectoryMap.dir_map[simulation.id]
        else:
            if save_dir_map:
                SimulationDirectoryMap.preload_experiment(simulation.experiment)
                return SimulationDirectoryMap.get_simulation_path(simulation, save_dir_map=False)
            else:
                return SimulationDirectoryMap.single_simulation_dir(simulation)

    @staticmethod
    def single_simulation_dir(simulation):
        exp = simulation.experiment
        if exp.location == "LOCAL":
            path = os.path.join(exp.sim_root, '%s_%s' % (exp.exp_name, exp.exp_id), simulation.id)
        else:
            from simtools.Utilities.COMPSUtilities import workdirs_from_simulations
            from simtools.Utilities.COMPSUtilities import get_simulation_by_id
            path = workdirs_from_simulations([get_simulation_by_id(simulation.id)])[simulation.id]
        SimulationDirectoryMap.dir_map[simulation.id] = path
        return path

    @staticmethod
    def preload_experiment(experiment):
        """
        Preload an experiment in the directory map.
        Used to retrieve the whole directory map.
        :param experiment:
        """
        if experiment.location == "HPC":
            from simtools.Utilities.COMPSUtilities import workdirs_from_experiment_id
            SimulationDirectoryMap.dir_map.update(workdirs_from_experiment_id(experiment.exp_id))
        else:
            for simulation in experiment.simulations:
                SimulationDirectoryMap.dir_map[simulation.id] = SimulationDirectoryMap.single_simulation_dir(simulation)
