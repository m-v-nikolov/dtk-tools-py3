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
                          threshold_type='COUNT', #this is the default, we can also look at % per eligible population
                          thresholds=[13, 254],
                          triggered_events=['Party', 'PartyHarder']
                          )


add_incidence_counter(cb,
                          start_day=50,
                          count_duration=30,
                          count_triggers=['HappyBirthday'],
                          thresholds=[1, 9],
                          triggered_events=['Party', 'PartyHarder']
                          )

# adding an intervention node IRS intervention that starts listening for Action1 trigger and when/if it hears it,
# listening_duration of -1 indicates that this intervention will listen forever and perform the tasks whenever Action1 is sent out
add_node_IRS(cb, 30,  trigger_condition_list=["Party"], listening_duration=-1)

# this intervention is distributed and starts listening on day 60, but distributes the IRS 1000 days after it is triggered
# please note if the listening duration was less than triggered day + campaign delay, the intervention would not run.
add_node_IRS(cb, 60, triggered_campaign_delay=1000, trigger_condition_list=["PartyHarder"])

# listens for 15 days and, as the result, hears nothing and does nothing.
add_node_IRS(cb, 60, trigger_condition_list=["PartyHarder"], listening_duration=15)



# run_sim_args is what the `dtk run` command will look for
run_sim_args =  {
    'exp_name': 'Example Event Counter and Triggered and Delayed IRS',
    'config_builder': cb
}



# If you prefer running with `python example_example_event_count_and_triggered_events.py`, you will need the following block
if __name__ == "__main__":
    SetupParser.init()
    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(**run_sim_args)
    # Wait for the simulations to be done
    exp_manager.wait_for_finished(verbose=True)
    assert(exp_manager.succeeded())
