import os  # mkdir, path, etc.
import json  # to read JSON output files
import numpy as np  # for reading spatial output data by node and timestep
import struct  # for binary file unpacking
import threading  # for multi-threaded job submission and monitoring
import pandas as pd  # for reading csv files

import logging

logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-10s) %(message)s')


class SimulationOutputParser(threading.Thread):
    def __init__(self, sim_dir, sim_id, sim_data, analyzers, semaphore=None):
        threading.Thread.__init__(self)
        self.sim_dir = sim_dir
        self.sim_id = sim_id
        self.sim_data = sim_data
        self.analyzers = analyzers
        self.raw_data = {}
        self.selected_data = {}
        self.semaphore = semaphore

    def run(self):
        try:
            # list of output files needed by any analysis
            filenames = set()
            for a in self.analyzers:
                filenames.update(a.filenames)
            filenames = list(filenames)

            # parse output files for analysis
            self.load_all_files(filenames)

            # do sim-specific part of analysis on parsed output data
            for analyzer in self.analyzers:
                self.selected_data[id(analyzer)] = analyzer.apply(self)

            del self.raw_data  # ?
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

    def load_single_file(self, filename, *args):
        file_extension = os.path.splitext(filename)[1][1:].lower()
        if file_extension == 'json':
            logging.debug('reading JSON')
            self.load_json_file(filename, *args)
        elif file_extension == 'csv':
            logging.debug('reading CSV')
            self.load_csv_file(filename, *args)
        elif file_extension == 'xlsx':
            logging.debug('reading XLSX')
            self.load_xlsx_file(filename, *args)
        elif file_extension == 'txt':
            logging.debug('reading txt')
            self.load_txt_file(filename, *args)
        elif file_extension == 'bin' and 'SpatialReport' in filename:
            self.load_bin_file(filename, *args)
        else:
            print(filename + ' is of an unknown type.  Skipping...')
            return

    def load_json_file(self, filename, *args):
        with open(self.get_path(filename)) as json_file:
            self.raw_data[filename] = json.loads(json_file.read())

    def load_csv_file(self, filename, *args):
        with open(self.get_path(filename)) as csv_file:
            self.raw_data[filename] = pd.read_csv(csv_file, skipinitialspace=True)

    def load_xlsx_file(self, filename, *args):
        excel_file = pd.ExcelFile(self.get_path(filename))
        self.raw_data[filename] = {sheet_name: excel_file.parse(sheet_name)
                                   for sheet_name in excel_file.sheet_names}

    def load_txt_file(self, filename, *args):
        try:
            self.raw_data[filename] = self.get_last_megabyte(filename)
        except:
            self.raw_data[filename] = 'Error reading file.'

    def load_bin_file(self, filename, *args):
        with open(self.get_path(filename), 'rb') as bin_file:
            data = bin_file.read(8)
            n_nodes, = struct.unpack('i', data[0:4])
            n_tstep, = struct.unpack('i', data[4:8])
            # print( "There are %d nodes and %d time steps" % (n_nodes, n_tstep) )

            nodeids_dtype = np.dtype([('ids', '<i4', (1, n_nodes))])
            nodeids = np.fromfile(bin_file, dtype=nodeids_dtype, count=1)
            nodeids = nodeids['ids'][:, :, :].ravel()
            # print( "node IDs: " + str(nodeids) )

            channel_dtype = np.dtype([('data', '<f4', (1, n_nodes))])
            channel_data = np.fromfile(bin_file, dtype=channel_dtype)
            channel_data = channel_data['data'].reshape(n_tstep, n_nodes)

        self.raw_data[filename] = {'n_nodes': n_nodes,
                                   'n_tstep': n_tstep,
                                   'nodeids': nodeids,
                                   'data': channel_data}

    def get_sim_dir(self):
        return os.path.join(self.sim_dir, self.sim_id)


class CompsDTKOutputParser(SimulationOutputParser):
    sim_dir_map = None
    use_compression = False

    @classmethod
    def enableCompression(cls):
        print('Enabling COMPS asset service compression')
        cls.use_compression = True

    @classmethod
    def createSimDirectoryMap(cls, exp_id=None, suite_id=None, save=True):
        from COMPS.Data import Experiment, Suite, QueryCriteria

        def workdirs_from_simulations(sims):
            return {sim.getId().toString(): sim.getHPCJobs().toArray()[-1].getWorkingDirectory() for sim in sims}

        def sims_from_experiment(e):
            print('Simulation working directories for ExperimentId = %s' % e.getId().toString())
            return e.GetSimulations(QueryCriteria().Select('Id').SelectChildren('HPCJobs')).toArray()

        def workdirs_from_experiment_id(exp_id):
            e = Experiment.GetById(exp_id)
            sims = sims_from_experiment(e)
            return workdirs_from_simulations(sims)

        def workdirs_from_suite_id(suite_id):
            print('Simulation working directories for SuiteId = %s' % suite_id)
            s = Suite.GetById(suite_id)
            exps = s.GetExperiments(QueryCriteria().Select('Id')).toArray()
            sims = []
            for e in exps:
                sims += sims_from_experiment(e)
            return workdirs_from_simulations(sims)

        if suite_id:
            sim_map = workdirs_from_suite_id(suite_id)
        elif exp_id:
            sim_map = workdirs_from_experiment_id(exp_id)
        else:
            raise Exception('Unable to map COMPS simulations to output directories without Suite or Experiment ID.')

        print('Populated map of %d simulation IDs to output directories' % len(sim_map))
        if save:
            cls.sim_dir_map = sim_map
        return sim_map

    def load_all_files(self, filenames):
        from COMPS.Data import Simulation, AssetType
        from java.util import ArrayList, UUID

        if self.sim_dir_map is not None:
            # sim_dir_map -> we can just open files locally...
            super(CompsDTKOutputParser, self).load_all_files(filenames)
            return

        # can't open files locally... we have to go through the COMPS asset service
        paths = ArrayList()
        for filename in filenames:
            paths.add(filename.replace('\\', '/'))

        assets = Simulation.RetrieveAssets(UUID.fromString(self.sim_id), AssetType.Output, paths, self.use_compression,
                                           None)
        asset_byte_arrays = assets.toArray() if assets else []

        # print('done retrieving files; starting load')

        for filename, byte_array in zip(filenames, asset_byte_arrays):
            self.load_single_file(filename, byte_array)

    def load_json_file(self, filename, *args):
        if self.sim_dir_map is not None:
            super(CompsDTKOutputParser, self).load_json_file(filename)
        else:
            jsonstr = args[0].tostring()
            self.raw_data[filename] = json.loads(jsonstr)

    def load_csv_file(self, filename, *args):
        if self.sim_dir_map is not None:
            super(CompsDTKOutputParser, self).load_csv_file(filename)
        else:
            from StringIO import StringIO
            csvstr = StringIO(args[0].tostring())
            self.raw_data[filename] = pd.read_csv(csvstr, skipinitialspace=True)
            #self.raw_data[filename] = args[0].tostring()

    def load_xlsx_file(self, filename, *args):
        excel_file = pd.ExcelFile( self.get_path(filename) )
        self.raw_data[filename] = {sheet_name: excel_file.parse(sheet_name) 
          for sheet_name in excel_file.sheet_names}

    def load_txt_file(self, filename, *args):
        if self.sim_dir_map is not None:
            super(CompsDTKOutputParser, self).load_txt_file(filename)
        else:
            str = args[0].tostring()
            self.raw_data[filename] = str

    def load_bin_file(self, filename, *args):
        if self.sim_dir_map is not None:
            super(CompsDTKOutputParser, self).load_bin_file(filename)
        else:
            arr = args[0]

            n_nodes, = struct.unpack('i', arr[0:4])
            n_tstep, = struct.unpack('i', arr[4:8])
            # print( "There are %d nodes and %d time steps" % (n_nodes, n_tstep) )

            nodeids = struct.unpack(str(n_nodes) + 'i', arr[8:8 + n_nodes * 4])
            nodeids = np.asarray(nodeids)
            # print( "node IDs: " + str(nodeids) )

            channel_data = struct.unpack(str(n_nodes * n_tstep) + 'f',
                                         arr[8 + n_nodes * 4:8 + n_nodes * 4 + n_nodes * n_tstep * 4])
            channel_data = np.asarray(channel_data)
            channel_data = channel_data.reshape(n_tstep, n_nodes)

            self.raw_data[filename] = {'n_nodes': n_nodes,
                                       'n_tstep': n_tstep,
                                       'nodeids': nodeids,
                                       'data': channel_data}

    def get_sim_dir(self):
        return self.sim_dir_map[self.sim_id]
