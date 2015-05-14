import time
import matplotlib.pyplot as plt

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.utils.core.DTKSetupParser import DTKSetupParser
from dtk.utils.simulation.SimulationManager import SimulationManagerFactory

from dtk.utils.analyzers.timeseries import TimeseriesAnalyzer
from dtk.utils.analyzers.select import example_selection
from dtk.utils.analyzers.group import group_all
from dtk.utils.analyzers.plot import plot_CI_bands

from dtk.vector.study_sites import configure_site
from dtk.vector.species import set_larval_habitat
from dtk.interventions.itn import add_ITN

def main():
    # CONFIGURE the simulation
    cb=DTKConfigBuilder.from_defaults('VECTOR_SIM')
    configure_site(cb, 'Sinazongwe')
    cb.set_param('Simulation_Duration', 5 * 365)  # five years

    # DEMO: mosquito species
    #arabiensis_extinction(cb)
    #arabiensis_with_small_constant_component(cb)
    arabiensis_funestus_vectors(cb)

    # DEMO: ITN campaign
    child_ITN_distribution(cb,coverage=0.9)
    #population_ITN_distribution(cb,coverage=0.9)

    run_sim_args =  {'config_builder': cb,
                     'exp_name': '1_vector_demo'}

    # RUN the simulation
    sm = SimulationManagerFactory.from_exe(DTKSetupParser().get('BINARIES','exe_path'),'LOCAL')
    sm.RunSimulations(**run_sim_args)

    # STATUS of simulation
    while True:
        states, msgs = sm.SimulationStatus()
        sm.printStatus(states,msgs)
        if sm.statusFinished(states): break
        else: time.sleep(5)

    # PLOT output of simulation
    analyzers = [ TimeseriesAnalyzer(
                    select_function=example_selection(start_date='1/1/2001'),
                    group_function=group_all,
                    plot_function=plot_CI_bands
                    ) ]

    for analyzer in analyzers:
        sm.AddAnalyzer(analyzer)
    sm.AnalyzeSimulations()

def arabiensis_extinction(cb):
    # Low-level An. arabiensis transmission with temporary rainfall-driven habitat only
    # leading to extinction during dry-season
    set_larval_habitat( cb, { 'arabiensis': { "TEMPORARY_RAINFALL": 4e8 } } )

def arabiensis_with_small_constant_component(cb):
    # Low-level An. arabiensis transmission with temporary rainfall-driven habitat
    # plus a small constant component leading to perpetuation through the dry-season
    set_larval_habitat( cb, { 'arabiensis': { "TEMPORARY_RAINFALL": 4e8,
                                              "CONSTANT"          : 5e7 } } )

def arabiensis_funestus_vectors(cb):
    # Multiple vector species: An. arabiensis and An. funestus
    # Tune parameters to observed biting rates by species, sporozoite rates
    set_larval_habitat( cb, { 'arabiensis': { "TEMPORARY_RAINFALL": 2e10,
                                              "CONSTANT"          : 1e7 },
                              'funestus'  : { "WATER_VEGETATION"  : 2e9} } )

def child_ITN_distribution(cb,coverage):
    # Distribute default ITN to under-5-yr-old children at specified coverage
    add_ITN(cb, start=3*365, coverage_by_ages=[{'coverage':coverage,'min':0,'max':5}])

def population_ITN_distribution(cb,coverage):
    # Distribute default ITN to all ages at specified coverage
    add_ITN(cb, start=3*365, coverage_by_ages=[{'coverage':coverage}])

if __name__ == '__main__':
    main()
    plt.show()
