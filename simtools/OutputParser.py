import gc  # for garbage collection
import json  # to read JSON output files
import logging
import os  # mkdir, path, etc.
import struct  # for binary file unpacking
import threading  # for multi-threaded job submission and monitoring
from io import StringIO, BytesIO

import numpy as np  # for reading spatial output data by node and timestep
import pandas as pd  # for reading csv files

from simtools.Utilities.COMPSUtilities import workdirs_from_experiment_id, get_simulation_by_id, \
    get_asset_files_for_simulation_id
from simtools.Utilities.COMPSUtilities import workdirs_from_suite_id

logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-10s) %(message)s')


class SimulationOutputParser(threading.Thread):
    def __init__(self, simulation, analyzers, semaphore=None, parse=True):
        threading.Thread.__init__(self)
        self.sim_id = simulation.id
        self._sim_path = None
        self.sim_data = simulation.tags
        self.experiment = simulation.experiment
        self.simulation = simulation
        self.analyzers = analyzers
        self.raw_data = {}
        self.selected_data = {}
        self.semaphore = semaphore
        self.parse = parse

    @property
    def sim_path(self):
        if not self._sim_path:
            self._sim_path = self.simulation.get_path()
        return self._sim_path

    def run(self):
        try:
            # list of output files needed by any analysis
            filenames = set()
            for a in self.analyzers:
                filenames.update(a.filenames)

            # parse output files for analysis
            self.load_all_files(filenames)

            # do sim-specific part of analysis on parsed output data
            for analyzer in self.analyzers:
                self.selected_data[id(analyzer)] = analyzer.apply(self)

            del self.raw_data
            gc.collect()  # clean up after apply()

        finally:
            if self.semaphore:
                self.semaphore.release()

    def get_path(self, filename):
        return os.path.join(self.get_sim_dir(), filename)

    def get_last_megabyte(self, filename):
        with open(self.get_path(filename)) as file:
            # Go to end of file.
            file.seek(0, os.SEEK_END)

            seekDistance = min(file.tell(), 1024 * 1024)
            file.seek(-1 * seekDistance, os.SEEK_END)

            return file.read()

    def load_all_files(self, filenames):
        for filename in filenames:
            self.load_single_file(filename)

    def load_single_file(self, filename, content=None):
        file_extension = os.path.splitext(filename)[1][1:].lower()

        if content is not None:
            content = BytesIO(content)
        else:
            with open(self.get_path(filename), 'rb') as output_file:
                content = BytesIO(output_file.read())

        if not self.parse:
            self.load_raw_file(filename, content)
        elif file_extension == 'json':
            logging.debug('reading JSON')
            self.load_json_file(filename, content)
        elif file_extension == 'csv':
            logging.debug('reading CSV')
            self.load_csv_file(filename, content)
        elif file_extension == 'xlsx':
            logging.debug('reading XLSX')
            self.load_xlsx_file(filename, content)
        elif file_extension == 'txt':
            logging.debug('reading txt')
            self.load_txt_file(filename, content)
        elif file_extension == 'bin' and 'SpatialReport' in filename:
            self.load_bin_file(filename, content)
        else:
            self.load_raw_file(filename, content)

    def load_json_file(self, filename, content):
        self.raw_data[filename] = json.load(content)

    def load_raw_file(self, filename, content):
        self.raw_data[filename] = content

    def load_csv_file(self, filename, content):
        if not isinstance(content, StringIO) and not isinstance(content, BytesIO):
            content = StringIO(content)

        csv_read = pd.read_csv(content, skipinitialspace=True)
        self.raw_data[filename] = csv_read

    def load_xlsx_file(self, filename, content):
        excel_file = pd.ExcelFile(content)
        self.raw_data[filename] = {sheet_name: excel_file.parse(sheet_name)
                                   for sheet_name in excel_file.sheet_names}

    def load_txt_file(self, filename, content):
        self.raw_data[filename] = str(content.getvalue().decode())

    def load_bin_file(self, filename, content):
        from dtk.tools.output.SpatialOutput import SpatialOutput
        so = SpatialOutput.from_bytes(content)
        self.raw_data[filename] = so.to_dict()

    def get_sim_dir(self):
        return self.sim_path


class CompsDTKOutputParser(SimulationOutputParser):
    sim_dir_map = None
    asset_service = True

    def __init__(self, simulation, analyzers, semaphore=None, parse=True):
        super(CompsDTKOutputParser, self).__init__(simulation, analyzers, semaphore, parse)
        self.COMPS_simulation = get_simulation_by_id(self.sim_id)

    @classmethod
    def createSimDirectoryMap(cls, exp_id=None, suite_id=None, save=True, comps_experiment=None, verbose=True):
        if suite_id and not exp_id:
            sim_map = workdirs_from_suite_id(suite_id)
        elif exp_id:
            sim_map = workdirs_from_experiment_id(exp_id, comps_experiment)
        else:
            raise Exception('Unable to map COMPS simulations to output directories without Suite or Experiment ID.')

        if verbose: print('Populated map of %d simulation IDs to output directories' % len(sim_map))

        if save:
            cls.sim_dir_map = cls.sim_dir_map or {}
            cls.sim_dir_map.update(sim_map)

        return sim_map

    def load_all_files(self, filenames):
        if not self.asset_service:
            #  we can just open files locally...
            super(CompsDTKOutputParser, self).load_all_files(filenames)
            return

        # Separate the path into asset collection and transient files
        assets = [path for path in filenames if path.lower().startswith("assets")]
        transient = [path for path in filenames if not path.lower().startswith("assets")]

        byte_arrays = {}

        if transient:
            try:
                byte_arrays.update(dict(zip(transient, self.COMPS_simulation.retrieve_output_files(paths=transient))))
            except RuntimeError:
                print("Could not retrieve requested file(s) for simulation {} - Requested files: {}. Parser exiting..."
                      .format(self.sim_id, transient))
                exit()

        if assets:
            try:
                byte_arrays.update(get_asset_files_for_simulation_id(self.sim_id, paths=assets, remove_prefix='Assets'))
            except RuntimeError:
                print("Could not retrieve requested file(s) for simulation {} - Requested files: {}. Parser exiting..."
                      .format(self.sim_id, assets))
                exit()

        for filename, byte_array in byte_arrays.items():
            self.load_single_file(filename, byte_array)

    def get_sim_dir(self):
        return self.sim_dir_map[self.sim_id]
