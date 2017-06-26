from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.vector.study_sites import configure_site
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser
from dtk.interventions.outbreakindividualdengue import add_OutbreakIndividualDengue

# This block will be used unless overridden on the command-line
SetupParser.default_block = 'EXAMPLE'

cb = DTKConfigBuilder.from_defaults('DENGUE_SIM')
configure_site(cb, 'Puerto_Rico')
cb.campaign["Campaign_Name"] = "Campaign - Outbreak"
add_OutbreakIndividualDengue(cb, 100, {'max': 1.725, 'min': 0}, 'Strain_1', [])
add_OutbreakIndividualDengue(cb, 5000, {}, 'Strain_2', [])
add_OutbreakIndividualDengue(cb, 5000, {}, 'Strain_3', [])
add_OutbreakIndividualDengue(cb, 5000, {}, 'Strain_4', [])

# cb.set_param('Simulation_Duration', 30*365)

run_sim_args = {'config_builder': cb,
                'exp_name': 'ExampleSim'}


if __name__ == "__main__":
    SetupParser.init(selected_block=SetupParser.default_block)
    exp_manager = ExperimentManagerFactory.from_setup()
    exp_manager.run_simulations(**run_sim_args)
