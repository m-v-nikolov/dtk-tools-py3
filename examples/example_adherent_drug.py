from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.vector.study_sites import configure_site
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from malaria.reports.MalariaReport import add_event_counter_report
from simtools.SetupParser import SetupParser
from dtk.interventions.adherent_drug import add_adherent_drug

# you will need to install malaria package for use with dtk-tools:
# use > dtk get_package malaria -v HEAD

# This block will be used unless overridden on the command-line
# this means that simtools.ini local block will be used
# change this to 'LOCAL' to run it on just your machine.
#SetupParser('HPC')

cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')
cb.update_params({"Genome_Markers": []})
cb.update_params({"Base_Population_Scale_Factor": 0.001}),
configure_site(cb, "Matsari")

# event counter can help you keep track of events that are happening that you're interested in.
add_event_counter_report(cb, ["Took_Dose", "NewClinicalCase"])

# run_sim_args is what the `dtk run` command will look for
run_sim_args =  {
    'exp_name': 'Matsari_Malaria_Adherence_Drug_Example',
    'config_builder': cb
}


# There are defaults for all the variables except the config_builder that gets passed in
# you could, if you wanted to, create this interventions with
# add_adherent_drug(cb)
safasfas
# You'll want to define the configuration for the usage/waning of the drug separately and pass the whole thing
# to adherence_config variable - there is a default, which is:
# {
#             "class": "WaningEffectMapLinearAge",
#             "Initial_Effect": 1.0,
#             "Durability_Map":
#                 {
#                     "Times": [0.0, 12.99999, 13.0, 125.0],
#                     "Values": [0.0, 0.0, 1.0, 1.0]
#                 }
#         }

# the map count that does the probability of taking this per dose (you'll have to know how many doses)
waning_effect_map_count = {
    "class": "WaningEffectMapCount",
    "Initial_Effect": 1.0,
    "Durability_Map":
        {
            "Times": [1.0, 2.0, 3.0, 4, 5, 6],
            "Values": [1, 0.8, 0.8, 0.6, 0.6, 0.2]
        }
}

# combination of the effects
waning_effect_combo ={
        "class" : "WaningEffectCombo", # the effects are multiplied
        "Effect_List" : [
            {
                "class": "WaningEffectMapLinearAge",
                "Initial_Effect" : 1.0,
                "Durability_Map" :
                {
                    "Times"  : [ 0.0,  5,  13.0, 125.0 ],
                    "Values" : [ 0.0,   0.0,       1.0,   1.0 ]
                }
            },
            {
                "class": "WaningEffectMapCount",
                "Initial_Effect" : 1.0,
                "Durability_Map" :
                {
                    "Times": [1.0, 2.0, 3.0, 4,    5,    6],
                    "Values": [1,  0.8, 0.8, 0.6, 0.6, 0.2]
                }
            },
            {
                "class": "WaningEffectExponential",
                "Initial_Effect": 1.0,
                "Decay_Time_Constant" : 7
            }
        ]
    }

# we are creating two campaigns. This ones gives out Arthemether to a person that has a NewClinicalCase Event happen to them
# We start listening for NewClinical case on day 1, with person having the probability of taking every doze according to the
# waning_effect_map_count defined above, we also delay the beginning of the taking of the drug by 5 days after we receive
# NewClinicalCase event. The campaign lasts for 50 time steps. The following defaults are used for the non-adherence:
#   non_adherence_options=["NEXT_UPDATE"],
#    non_adherence_distribution=[1]
add_adherent_drug(cb, start=25, drug_type="Artemether", adherence_config=waning_effect_map_count,
                  triggered_campaign_delay=5, trigger_condition_list=["NewClinicalCase"],
                  listening_duration=75)

# in this campaign that starts on day 200 and gives everyone Artemether with the adherence defined by the waning_effect_combo
# above, we repeat this twice with second campaign running 30 time steps later, we are defining the non_adherence_options to have
# probabilities of people stopping altogether being at 30% and people taking the drug at the next update at 70%
# dont allow duplicates is 1 by default so the second wave of the campaign would be given only to people who didn't recieve the first wave
# those just born
add_adherent_drug(cb, start=200, drug_type="Artemether", adherence_config=waning_effect_combo, non_adherence_options=["NEXT_UPDATE", "STOP"],
                  non_adherence_distribution=[0.7,0.3],
                  number_repetitions=2, timesteps_between_repititions=30)



# If you prefer running with `python example_example_event_count_and_triggered_events.py`, you will need the following block
if __name__ == "__main__":
    SetupParser.init()
    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(**run_sim_args)
    # Wait for the simulations to be done
    exp_manager.wait_for_finished(verbose=True)
    assert(exp_manager.succeeded())