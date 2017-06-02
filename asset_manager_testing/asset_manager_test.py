from simtools.SetupParser import SetupParser
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.utils.reports.CustomReport import BaseReport
from dtk.vector.study_sites import configure_site

from simtools.AssetManager.SimulationAssets import SimulationAssets

BAR = "".join(['-' for i in range(80)])

# def COMPS_login(endpoint):
#     try:
#         Client.auth_manager()
#     except:
#         Client.login(endpoint)

# SetupParser.init('AM')
# COMPS_login(SetupParser.get('server_endpoint'))

# from example_sim.py
cb = DTKConfigBuilder.from_defaults('VECTOR_SIM')

configure_site(cb, 'Namawala')
cb.add_reports(BaseReport(type="VectorHabitatReport"))

#cb.add_reports(BaseReport(type="ReportVectorStats"))
#cb.add_reports(BaseReport(type="ReportVectorMigration"))

# required items for dtk commands
config_builder = cb
run_sim_args =  {
    'exp_name': 'ExampleSim',
}


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

if __name__ == "__main__":
    from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory

    SetupParser.init('AM')

    exp_manager = ExperimentManagerFactory.from_setup(config_builder=config_builder)
    exp_manager.run_simulations(**run_sim_args)
