import json
import logging

import utils
from simtools.DataAccess.DataStore import DataStore

logger = logging.getLogger(__name__)


class SimulationMonitor(object):
    """
    A class to monitor the status of local simulation.
    Threads are spawned to query each simulation in parallel.
    """

    def __init__(self, exp_id):
        self.exp_id = exp_id

    def query(self):
        states, msgs = {}, {}
        experiment = DataStore.get_experiment(self.exp_id)
        for sim in experiment.simulations:
            states[sim.id] = sim.status if sim.status else "Waiting"
            msgs[sim.id] = sim.message if sim.message else ""
        return states, msgs


class CompsSimulationMonitor(SimulationMonitor):
    """
    A class to monitor the status of COMPS simulations.
    Note that only a single thread is spawned as the COMPS query is based on the experiment ID
    """

    def __init__(self, exp_id, suite_id, endpoint):
        self.exp_id = exp_id
        self.suite_id = suite_id
        self.server_endpoint = endpoint

    def query(self):
        from COMPS.Data import Experiment, Suite, QueryCriteria
        utils.COMPS_login(self.server_endpoint)

        def sims_from_experiment(e):
            # logger.info('Monitoring simulations for ExperimentId = %s', e.getId().toString())
            return e.GetSimulations(QueryCriteria().Select('Id,SimulationState')).toArray()

        def sims_from_experiment_id(exp_id):
            e = Experiment.GetById(exp_id)
            return sims_from_experiment(e)

        def sims_from_suite_id(suite_id):
            #logger.info('Monitoring simulations for SuiteId = %s', suite_id)
            s = Suite.GetById(suite_id)
            exps = s.GetExperiments(QueryCriteria().Select('Id')).toArray()
            sims = []
            for e in exps:
                sims += sims_from_experiment(e)
            return sims

        if self.suite_id:
            sims = sims_from_suite_id(self.suite_id)
        elif self.exp_id:
            sims = sims_from_experiment_id(self.exp_id)
        else:
            raise Exception(
                'Unable to monitor COMPS simulations as metadata contains no Suite or Experiment ID:\n'
                '(Suite ID: %s, Experiment ID:%s)' % (self.suite_id, self.exp_id))

        states, msgs = {}, {}
        for sim in sims:
            id_string = sim.getId().toString()
            states[id_string] = sim.getState().toString()
            msgs[id_string] = ''

        return states, msgs
