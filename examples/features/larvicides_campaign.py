import os

from dtk.interventions.larvicides import add_larvicides
from dtk.utils.analyzers import TimeseriesAnalyzer, group_by_name
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from simtools.ModBuilder import ModBuilder

# Create a config builder from set of input files
input_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),"input")
cb = DTKConfigBuilder.from_files(os.path.join(input_dir,'config.json'), os.path.join(input_dir,'campaign.json'))

# Change the duration of the simulations to 5 years
cb.set_param('Simulation_Duration', 5*365)


# Define a set_larvicides function in order for the builder to call with different values
# Functions passed to the builder needs to take a ConfigBuilder as first parameter
# Here we are interested on sweeping on the start date of the intervention.
def set_larvicides(cb, start):
    # Add larvicides to the campaign held in the ConfigBuilder
    add_larvicides(cb,start)

    # Returns the tag we want our simulation to have
    # In order to identify which value of the sweep we used, we are tagging our simulations
    # with larvicide_start = start date of the larvicides intervention
    return {"larvicide_start": start}

# Create a builder from a list of array of function.
# Basically we are creating:
# [set_larvicides(cb,0), set_larvicides(cb,5), ... , set_larvicides(cb,730)],
# [cb.set_param('Run_Number',0), ..., cb.set_param('Run_Number',4)]
# Each array are holding functions that modify the base simulation. A cartesian product will happen to explore all
# the possible combination. Basically giving 25 simulations with:
# +-------------------+----------------+
# | larvicide_start   |   Run_Number   |
# +-------------------+----------------+
# | 0                 | 0              |
# | 5                 | 0              |
# | 10                | 0              |
# | ...               | ...            |
# | 5                 | 1              |
# | 10                | 1              |
# | 365               | 1              |
# | ...               | ...            |
# | 365               | 4              |
# | 730               | 4              |
# +-------------------+----------------+
builder = ModBuilder.from_combos(
    [ModBuilder.ModFn(set_larvicides, start_time ) for start_time in (0,5,10, 365, 730)],
    [ModBuilder.ModFn(DTKConfigBuilder.set_param, 'Run_Number', seed) for seed in range(5)],
)

# The run_sim_args is a dictionary informing the command line of:
# - What config builder to use
# - What is the name we want for the experiment
# - Which experiment builder to use
run_sim_args = {'config_builder': cb,
                'exp_name': 'Sample larvicides epxeriment',
                'exp_builder': builder}

# In this file we also decided to include the analyzers.
# When present the `analyzers` variable is an array of Analyzers that will be executed when
# the command `dtk analyze larvicides_campaign.py` is called.
# Here we are using a simple TimeSeriesAnalyzer, grouping the simulations by the larvicide_start tag (averaging
# across the Run_Number). And displaying the results for 3 vector related channels.
analyzers = [
                TimeseriesAnalyzer(group_function=group_by_name('larvicide_start'),
                                   channels=['Daily EIR', 'Adult Vectors', 'Infected'])
            ]


