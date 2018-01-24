import itertools

import os

from simtools.Analysis.OutputParser import SimulationOutputParser
from simtools.Utilities.COMPSCache import COMPSCache
from simtools.Utilities.COMPSUtilities import COMPS_login


def retrieve_data(simulation, analyzers, cache):
    # Filter first and get the filenames from filtered analysis
    filtered_analysis = [a for a in analyzers if a.filter(simulation)]
    filenames = set(itertools.chain(*(a.filenames for a in filtered_analysis)))

    # We dont have anything to do :)
    if not filenames or not filtered_analysis: return

    if simulation.experiment.location == "HPC":
        COMPS_login(simulation.experiment.endpoint)
        COMPS_simulation = COMPSCache.simulations(simulation.id)
        byte_arrays = COMPS_simulation.retrieve_output_files(paths=filenames)
    else:
        byte_arrays = []
        for filename in filenames:
            path = os.path.join(simulation.get_path(), filename)
            with open(path, 'rb') as output_file:
                byte_arrays.append(output_file.read())

    raw_data = {}
    for filename, content in zip(filenames, byte_arrays):
        raw_data[filename] = SimulationOutputParser.parse(filename, content)

    selected_data = {}
    for analyzer in filtered_analysis:
        selected_data[analyzer.uid] = analyzer.select_simulation_data(raw_data, simulation)

    cache.set(simulation.id, selected_data)
