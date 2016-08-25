from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.vector.study_sites import configure_site
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser
from dtk.interventions.outbreakindividualdengue import add_OutbreakIndivisualDengue

# For example only -- Force the selected block to be EXAMPLE
SetupParser("EXAMPLE")

cb = DTKConfigBuilder.from_defaults('DENGUE_SIM')
configure_site(cb, 'Puerto_Rico')
cb.campaign["Campaign_Name"] = "Campaign - Outbreak"
add_OutbreakIndivisualDengue(cb, 100, {'max': 1.725, 'min': 0}, 'Strain_1', [])
add_OutbreakIndivisualDengue(cb, 5000, {}, 'Strain_2', [])
add_OutbreakIndivisualDengue(cb, 5000, {}, 'Strain_3', [])
add_OutbreakIndivisualDengue(cb, 5000, {}, 'Strain_4', [])

# cb.set_param('Simulation_Duration', 30*365)

run_sim_args = {'config_builder': cb,
                'exp_name': 'ExampleSim'}


if __name__ == "__main__":
    sm = ExperimentManagerFactory.from_setup(SetupParser())
    sm.run_simulations(**run_sim_args)
