import itertools

from simtools.ExperimentManager.CompsExperimentManager import CompsExperimentManager
from simtools.SetupParser import SetupParser
from simtools.Utilities.General import CommandlineGenerator


class Builder:
    def __init__(self, name, description="", static_parameters={}, dynamic_parameters={}, setup=SetupParser('HPC'),
                 suite_id=None, experiment_tags={}, simulations_tags={}, simulations_name=None,
                 simulations_description=None):
        # Store general info
        self.setup = setup
        self.name = name
        self.description = description
        self.experiment_tags = experiment_tags
        self._experiment_configuration = self._simulation_configuration = self._plugin_info = None

        # If no specific simulation info -> get from the experiment
        self.simulation_name = simulations_name or self.name
        self.simulation_description = simulations_description or self.description
        self.simulation_tags = simulations_tags or self.experiment_tags

        # Handle the suite_id
        if not suite_id:
            self.suite_id = CompsExperimentManager.create_suite(name)
            self.generated_suite = True
        else:
            self.generated_suite = False
            self.suite_id = suite_id

        # Create the command line
        exe_options = {'--config': 'config.json', '--input-path': setup.get('input_root')}
        if self.setup.get('python_path') != '':
            exe_options['--python-script-path'] = setup.get('python_path')
        self.cmd = CommandlineGenerator(setup.get('bin_staging_root'), exe_options, [])

        # Flow control
        self.SimulationCreationLimit = -1
        self.SimulationCommissionLimit = -1

        # Parameters
        self.static_parameters = static_parameters
        self.dynamic_parameters = dynamic_parameters

    @property
    def experiment_configuration(self):
        return {
            "Configuration": {
                "NodeGroupName": self.setup.get('node_group'),
                "SimulationInputArgs": self.cmd.Options,
                "WorkingDirectoryRoot": self.setup.get('sim_root'),
                "ExecutablePath": self.cmd.Executable,
                "MaximumNumberOfRetries": 1,
                "Priority": self.setup.get('priority'),
                "MinCores": 1,
                "MaxCores": 1,
                "Exclusive": 0
            },
            "SuiteId": self.suite_id,
            "Name": self.name,
            "Description": self.description,
            "Tags": self.experiment_tags
        }

    @property
    def simulation_configuration(self):
        return {
            "Name": self.simulation_name,
            "Description": self.simulation_description,
            "Tags": self.simulation_tags
        }

    @property
    def plugin_info(self):
        # Prepare the table
        run_numbers = self.dynamic_parameters.pop('Run_Numbers') if 'Run_Numbers' in self.dynamic_parameters else [1]

        return {
            "Target": "BuilderPlugin",
            "Metadata": {"Name": "BasicBuilderPlugin", "Version": "2.0.0.0"},
            "Content":
                {
                    "Static_Parameters": self.static_parameters,
                    "Dynamic_Parameters":
                        {
                            "Run_Numbers": run_numbers,
                            "Header": [k for k in self.dynamic_parameters.keys()],
                            "Table": [element for element in itertools.product(*self.dynamic_parameters.values())]
                        }
                }
        }

    @property
    def wo(self):
        return {
            "WorkItem_Type": "Builder",
            "InputDirectoryRoot": self.setup.get('input_root'),
            "EntityMetadata":
                {
                    "Experiment": self.experiment_configuration,
                    "Simulation": self.simulation_configuration

                },
            "FlowControl":
                {
                    "SimulationCreationLimit": self.SimulationCreationLimit,
                    "SimulationCommissionLimit": self.SimulationCommissionLimit
                },
            "PluginInfo": [self.plugin_info]
        }
