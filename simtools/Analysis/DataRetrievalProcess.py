import itertools

import os
import traceback

from simtools.Analysis.OutputParser import SimulationOutputParser
from simtools.Utilities.COMPSCache import COMPSCache
from simtools.Utilities.COMPSUtilities import COMPS_login


def retrieve_data(simulation, analyzers, cache):
    # Filter first and get the filenames from filtered analysis
    filtered_analysis = [a for a in analyzers if a.filter(simulation)]
    filenames = set(itertools.chain(*(a.filenames for a in filtered_analysis)))

    # We dont have anything to do :)
    if not filenames or not filtered_analysis:
        cache.set(simulation.id, None)
        return

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

    # Get the raw data as a dictionary associating filename=>content
    raw_data = dict(zip(filenames, byte_arrays))

    # Selected data will be a dict with analyzer.uid => data
    selected_data = {}
    for analyzer in filtered_analysis:
        # If the analyzer needs the parsed data, parse
        if analyzer.parse:
            data = {filename:SimulationOutputParser.parse(filename, content) for filename, content in raw_data.items()}
        else:
            # If the analyzer doesnt wish to parse, give the raw data
            data = raw_data

        # Retrieve the selected data for the given analyzer
        try:
            selected_data[analyzer.uid] = analyzer.select_simulation_data(data, simulation)
        except:
            tb = traceback.format_exc()
            from simtools.Analysis.AnalyzeManager import EXCEPTION_KEY
            cache.set(EXCEPTION_KEY, {"a": analyzer, "s": simulation, "tb": tb})
            return

    # Store in the cache
    cache.set(simulation.id, selected_data)
