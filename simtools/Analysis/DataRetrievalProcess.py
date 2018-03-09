import itertools

import os
import traceback

from simtools.Analysis.OutputParser import SimulationOutputParser
from simtools.Utilities.COMPSCache import COMPSCache
from simtools.Utilities.COMPSUtilities import COMPS_login, get_asset_files_for_simulation_id


def retrieve_data(simulation, analyzers, cache):
    from simtools.Analysis.AnalyzeManager import EXCEPTION_KEY

    # Filter first and get the filenames from filtered analysis
    filtered_analysis = [a for a in analyzers if a.filter(simulation)]
    filenames = set(itertools.chain(*(a.filenames for a in filtered_analysis)))

    # We dont have anything to do :)
    if not filenames or not filtered_analysis:
        cache.set(simulation.id, None)
        return

    # The byte_arrays will associate filename with content
    byte_arrays = {}

    try:
        if simulation.experiment.location == "HPC":
            COMPS_login(simulation.experiment.endpoint)
            COMPS_simulation = COMPSCache.simulation(simulation.id)
            assets = [path for path in filenames if path.lower().startswith("assets")]
            transient = [path for path in filenames if not path.lower().startswith("assets")]
            if transient:
                byte_arrays.update(dict(zip(transient, COMPS_simulation.retrieve_output_files(paths=transient))))
            if assets:
                byte_arrays.update(get_asset_files_for_simulation_id(simulation.id, paths=assets, remove_prefix='Assets'))

        else:
            byte_arrays = []
            for filename in filenames:
                path = os.path.join(simulation.get_path(), filename)
                with open(path, 'rb') as output_file:
                    byte_arrays[filename] = output_file.read()
    except:
        tb = traceback.format_exc()
        cache.set(EXCEPTION_KEY, "An exception has been raised during data retrieval.\n"
                                 "Simulation: {} \n"
                                 "Analyzers: {}\n"
                                 "Files: {}\n"
                                 "\n{}".format(simulation, ", ".join(analyzers), ", ".join(filenames), tb))
        return

    # Selected data will be a dict with analyzer.uid => data
    selected_data = {}
    for analyzer in filtered_analysis:
        # If the analyzer needs the parsed data, parse
        if analyzer.parse:
            data = {filename:SimulationOutputParser.parse(filename, content)
                    for filename, content in byte_arrays.items()}
        else:
            # If the analyzer doesnt wish to parse, give the raw data
            data = byte_arrays

        # Retrieve the selected data for the given analyzer
        try:
            selected_data[analyzer.uid] = analyzer.select_simulation_data(data, simulation)
        except:
            tb = traceback.format_exc()
            cache.set(EXCEPTION_KEY, "An exception has been raised during data processing.\n"
                                     "Simulation: {} \n"
                                     "Analyzer: {}\n"
                                     "\n{}".format(simulation, analyzer, tb))
            return

    # Store in the cache
    cache.set(simulation.id, selected_data)
