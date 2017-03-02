from simtools.ExperimentManager.CompsExperimentManager import CompsExperimentManager
from simtools.SetupParser import SetupParser

builder_structure = {
    "WorkItem_Type": "Builder",
    "InputDirectoryRoot": "",
"EntityMetadata":{
"Experiment":{
    "Configuration":{},
"SuiteId": "",
                        "Name": "",
                        "Description": "",
}
}
}

class Builder:

    def __init__(self, name, static_parameters=[], dynamic_parameters=[], setup=SetupParser('HPC'), suite_id=None):
        self.setup = setup
        self.suite_id = suite_id if suite_id else CompsExperimentManager.create_suite(name)
        self.experiment_configuration = {}
        self.simulation_configuration = {}
        self.plugin_content = {}

        self.SimulationCreationLimit = -1
        self.SimulationCommissionLimit = -1

        self.static_parameters = static_parameters
        self.dynamic_parameters = dynamic_parameters


    def generate_wo(self):
        return     {
        "WorkItem_Type": "Builder",
        "InputDirectoryRoot": "",
        "EntityMetadata":
            {
                "Experiment":
                    {
                        "Configuration":
                            {
                                "NodeGroupName": "",
                                "SimulationInputArgs": "--config config.json --input-path $COMPS_PATH(USER)\\input\\Typhoid\\ -P $COMPS_PATH(USER)\\input\\Python_Scripts\\",
                                "WorkingDirectoryRoot": "$COMPS_PATH(USER)\\output\\TyphoidTest\\simulations",
                                "ExecutablePath": "$COMPS_PATH(USER)\\bin\\Eradication_2_23.exe",
                                "MaximumNumberOfRetries": 1,
                                "Priority": "Normal",
                                "MinCores": 1,
                                "MaxCores": 1,
                                "Exclusive": 0
                            },
                        "SuiteId": "fc2f6dd3-b0fe-e611-9400-f0921c16849c",
                        "Name": "Age distribution/vaccination fitting",
                        "Description": "Age distribution/vaccination fitting",
                        "Tags":
                            {
                                "OptimTool": "",
                                "SSMT": "",
                                "Typhoid": ""
                            }
                    },
                "Simulation":
                    {
                        "Name": "Age distribution/vaccination fitting",
                        "Description": "Age distribution/vaccination fitting",
                        "Tags":
                            {
                                "OptimTool": "",
                                "SSMT": "",
                                "Typhoid": ""
                            }
                    }
            },
        "FlowControl":
            {
                "SimulationCreationLimit": -1,
                "SimulationCommissionLimit": -1
            },
        "PluginInfo": [
            {
                "Target": "BuilderPlugin",
                "Metadata":
                    {
                        "Name": "BasicBuilderPlugin",
                        "Version": "2.0.0.0"
                    },
                "Content":
                    {
                        "Static_Parameters":
                            {
                                "CONFIG.Geography": "Santiago",
                                "CONFIG.Base_Population_Scale_Factor": 0.059999999999999998
                            },
                        "Dynamic_Parameters":
                            {
                                "Run_Numbers": [1, 2, 3, 4, 5],
                                "Header": ["CONFIG.Typhoid_Contact_Exposure_Rate",
                                           "CONFIG.Typhoid_Symptomatic_Fraction",
                                           "CONFIG.Typhoid_Protection_Per_Infection",
                                           "CONFIG.Typhoid_Acute_Infectiousness", "CONFIG.Typhoid_Exposure_Lambda",
                                           "CONFIG.Run_Number", "CONFIG.Campaign_Filename", "Scenario"],
                                "Table":
                                    [
                                        [0.017771434473542298, 0.01, 1, 7966.6097869469158, 0.12986263726771602, 96864, "campaign_baseline.json", "Baseline"],
                                    ]
                            }
                    }
            }]
    }
