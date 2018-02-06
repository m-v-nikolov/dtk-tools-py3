# This script will display the disk space of all experiments of the environment
# It uses pyCOMPS directly as there is no dtk-tools way to handle that for now
import itertools
import os
import sys
import time
from multiprocessing.pool import Pool

import pandas as pd
from COMPS.Data import Experiment, QueryCriteria
from diskcache import FanoutCache

from simtools.SetupParser import SetupParser
from simtools.Utilities.COMPSUtilities import COMPS_login
from simtools.Utilities.General import file_size, animation

# How many experiments to display in the TOP?
TOP_COUNT = 15

# Usernames
OWNERS = ["braybaud", "smoore62", "k.jamessoda"]

# By default we prefer using the cache over querying COMPS
FORCE_REFRESH = False


def get_experiment_info(experiment, cache):
    """
    Adds the experiment information for a given experiment to the cache:
    - raw_size: the size in bytes
    - size: the formatted size (in KB, MB or GB)
    - sims: the number of simulations
    This function is used by the process pool to parallelize the retrieval of experiment info

    :param experiment: The experiment to analyze
    """
    if experiment in cache and not FORCE_REFRESH:
        return

    # Login to COMPS
    COMPS_login("https://comps.idmod.org")
    try:
        simulations = experiment.get_simulations(
            query_criteria=QueryCriteria().select(['id']).select_children(['hpc_jobs']))
    except KeyError:
        cache.set(experiment, None)
        return

    size = sum(s.hpc_jobs[0].output_directory_size for s in simulations if s.hpc_jobs)
    cache.set(experiment, {
        "size": file_size(size),
        "sims": len(simulations),
        "raw_size": size
    })


def exp_str(experiment, info, display_owner=True):
    """
    Format an experiment and its information to a string.
    """
    string = "{} ({})".format(experiment.name, experiment.id)
    if display_owner:
        string += " - {}".format(experiment.owner)

    string += " : {} in {} simulations".format(info['size'], info['sims'])
    return string


def top_10_experiments(experiments_info):
    """
    Displays the top 10 of all experiments analyzed
    """
    print("Top {} Experiments".format(TOP_COUNT))

    for order, exp in enumerate(sorted(experiments_info, key=lambda i: experiments_info[i]["raw_size"], reverse=True)[:TOP_COUNT]):
        info = experiments_info[exp]
        print("{}. {}".format(order+1, exp_str(exp, info)))


def total_size_per_user(experiments_info):
    """
    Displays the total disk space occupied per user
    """
    print("Size per user")
    size_per_users = {}
    for experiment, info in experiments_info.items():
        if experiment.owner not in size_per_users:
            size_per_users[experiment.owner] = 0

        size_per_users[experiment.owner] += info["raw_size"]

    for order, owner in enumerate(sorted(size_per_users, key=size_per_users.get, reverse=True)):
        print("{}. {} with a total of {}".format(order+1, owner, file_size(size_per_users[owner])))


def top_10_experiments_per_user(experiments_info):
    """
    Display the top 10 biggest experiments per user
    """
    experiments_per_owner = {}

    for experiment, info in experiments_info.items():
        if experiment.owner not in experiments_per_owner:
            experiments_per_owner[experiment.owner] = {}

        experiments_per_owner[experiment.owner][experiment] = info

    for owner, experiments in experiments_per_owner.items():
        print("Top {} experiments for {}".format(TOP_COUNT, owner))
        for order, experiment in enumerate(sorted(experiments, key=lambda e: experiments[e]["raw_size"], reverse=True)[:TOP_COUNT]):
            print("{}. {}".format(order+1, exp_str(experiment, experiments[experiment], False)))
        print("")


if __name__ == "__main__":
    # Login to COMPS
    SetupParser.init('HPC')

    # Create/open the cache
    current_folder = os.path.dirname(os.path.realpath(__file__))
    cache_folder = os.path.join(current_folder, "cache")
    cache = FanoutCache(shards=6, directory=cache_folder)

    # This will hold all experiments info
    experiments_info = {}

    # All experiments
    all_experiments = list(itertools.chain(*(Experiment.get(query_criteria=QueryCriteria().where(["owner={}".format(owner)]))
                                      for owner in OWNERS)))

    all_experiments_len = len(all_experiments)

    # Create the pool of worker
    p = Pool(6)
    r = p.starmap_async(get_experiment_info, itertools.product(all_experiments, (cache,)))
    p.close()

    print("Analyzing disk space for:")
    print(" | {} experiments".format(all_experiments_len))
    print(" | Users: {}".format(", ".join(OWNERS)))

    # Wait for completion and display progress
    sys.stdout.write(" | Experiment analyzed: 0/{}".format(all_experiments_len))
    sys.stdout.flush()

    # While we are analyzing, display the status
    while not r.ready():
        remaining = r._number_left * r._chunksize
        remaining = remaining if remaining >= 0 else 0
        sys.stdout.write("\r {} Experiment analyzed: {}/{}".format(next(animation), all_experiments_len-remaining, all_experiments_len))
        sys.stdout.flush()

        time.sleep(.5)

    sys.stdout.write("\r | Experiment analyzed: {}/{}".format(all_experiments_len, all_experiments_len))
    sys.stdout.flush()

    # Get all the results
    experiments_info = {e:cache[e] for e in all_experiments and cache[e]}
    cache.close()

    # Display
    print("\n\n---------------------------")
    top_10_experiments(experiments_info)
    print("\n---------------------------")
    total_size_per_user(experiments_info)
    print("\n---------------------------")
    top_10_experiments_per_user(experiments_info)

