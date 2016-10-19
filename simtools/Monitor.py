import json
from collections import Counter

import utils
from simtools.DataAccess.DataStore import DataStore

logger = utils.init_logging('Monitor')


class SimulationMonitor(object):
    """
    A class to monitor the status of local simulation.
    Threads are spawned to query each simulation in parallel.
    """

    def __init__(self, exp_id):
        logger.debug("Create a LOCAL Monitor with exp_id=%s" % exp_id)
        self.exp_id = exp_id

    def query(self):
        logger.debug("Query the LOCAL Monitor for Experiment %s" % self.exp_id)
        states, msgs = {}, {}
        experiment = DataStore.get_experiment(self.exp_id)
        for sim in experiment.simulations:
            states[sim.id] = sim.status if sim.status else "Waiting"
            msgs[sim.id] = sim.message if sim.message else ""
        logger.debug("States returned")
        logger.debug(json.dumps(dict(Counter(states.values())), indent=3))
        return states, msgs


class CompsSimulationMonitor(SimulationMonitor):
    """
    A class to monitor the status of COMPS simulations.
    Note that only a single thread is spawned as the COMPS query is based on the experiment ID
    """

    def __init__(self, exp_id, suite_id, endpoint):
        logger.debug("Create a COMPS Monitor with exp_id=%s, suite_id=%s, endpoint=%s" % (exp_id,suite_id,endpoint))
        self.exp_id = exp_id
        self.suite_id = suite_id
        self.server_endpoint = endpoint

    def query(self):
        logger.debug("Query the HPC Monitor for Experiment %s" % self.exp_id)
        from COMPS.Data import Suite, QueryCriteria, Simulation
        utils.COMPS_login(self.server_endpoint)

        def sims_from_experiment(e):
            # logger.info('Monitoring simulations for ExperimentId = %s', e.getId().toString())
            return e.GetSimulations(QueryCriteria().Select('Id,SimulationState')).toArray()

        def sims_from_experiment_id(exp_id):
            return Simulation.Get(QueryCriteria().Where('ExperimentId=%s'%exp_id)).toArray()
            # e = Experiment.GetById(exp_id)
            # return sims_from_experiment(e)

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
            state_string = sim.getState().toString()
            if state_string not in ('Waiting', 'Commissioned', 'Running', 'Succeeded', 'Failed',  'Canceled', 'CancelRequested',
                         "Retry", "CommissionRequested", "Provisioning", "Created"):
                logger.warn("Failed to retrieve correct status for simulation %s. Status returned: %s" % state_string)
                continue
            states[id_string] = state_string
            msgs[id_string] = ''

        logger.debug("States returned")
        logger.debug(json.dumps(dict(Counter(states.values())), indent=3))

        return states, msgs
