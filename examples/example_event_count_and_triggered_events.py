from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.vector.study_sites import configure_site
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser
from dtk.interventions.incidence_counter import add_incidence_counter
from dtk.interventions.irs import add_node_IRS
from malaria.reports.MalariaReport import add_event_counter_report # you need to isntall the malaria package

# This block will be used unless overridden on the command-line
# this means that simtools.ini local block will be used
SetupParser.default_block = 'LOCAL'

cb = DTKConfigBuilder.from_defaults('VECTOR_SIM')
configure_site(cb, 'Namawala')

# event counter can help you keep track of events that are happening
add_event_counter_report(cb, ["HappyBirthday", "Party", "PartyHarder", "IRS_Blackout_Event_Trigger"])
# adding an incidence counter, which starts on day 20, and counts "Happy Birthday" events for 30 days.
# the default thresholds are 10 and 100 event counts and default events being sent out when the threshold is reached are Action1 and Action2
add_incidence_counter(cb,
                          start_day=20,
                          count_duration=30,
                          count_triggers=['HappyBirthday'],
                          threshold_type='COUNT',
                          thresholds=[13, 254],
                          triggered_events=['Party', 'PartyHarder'],
                          coverage=1,
                          repetitions=1,
                          tsteps_btwn_repetitions=365,
                          target_group='Everyone',
                          nodeIDs=[],
                          node_property_restrictions=[],
                          ind_property_restrictions=[]
                          )


add_incidence_counter(cb,
                          start_day=50,
                          count_duration=30,
                          count_triggers=['HappyBirthday'],
                          threshold_type='COUNT',
                          thresholds=[1, 9],
                          triggered_events=['Party', 'PartyHarder'],
                          coverage=1,
                          repetitions=1,
                          tsteps_btwn_repetitions=365,
                          target_group='Everyone',
                          nodeIDs=[],
                          node_property_restrictions=[],
                          ind_property_restrictions=[]
                          )

# adding an intervention node IRS intervention that starts listening for Action1 trigger and when/if it hears it,
#  it sprays the node with IRS, which costs 1 and marks node as not eligible for sptraying for 30 days,
# listening_duration of -1 indicates that this intervention will listen forever and perform the tasks whenever Action1 is sent out
add_node_IRS(cb, 30, initial_killing=0.5, box_duration=90, cost=1,
            trigger_condition_list=["Party"], listening_duration=-1)

# this campaign starts listening on day 60, but runs the campaign 1000 days after it is triggered
# please note if the listening duration was less than triggered day + camaign delay, the intervention would not run.
add_node_IRS(cb, 60, initial_killing=0.5, box_duration=90, cost=1, triggered_campaign_delay=1000,
            trigger_condition_list=["PartyHarder"])

# listens for 10 days and, as the result, hears nothing and does nothing.
add_node_IRS(cb, 60, initial_killing=0.5, box_duration=90, cost=1,
            trigger_condition_list=["PartyHarder"], listening_duration=15)



# run_sim_args is what the `dtk run` command will look for
run_sim_args =  {
    'exp_name': 'ExampleSim',
    'config_builder': cb
}



# If you prefer running with `python example_sim.py`, you will need the following block
if __name__ == "__main__":
    SetupParser.init()
    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(**run_sim_args)
    # Wait for the simulations to be done
    exp_manager.wait_for_finished(verbose=True)
    assert(exp_manager.succeeded())
