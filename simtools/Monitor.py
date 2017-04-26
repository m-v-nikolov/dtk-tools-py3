import json
from collections import Counter

from simtools.DataAccess.DataStore import DataStore
from simtools.Utilities.COMPSUtilities import sims_from_suite_id, sims_from_experiment_id, COMPS_login
from simtools.Utilities.General import init_logging, retry_function
logger = init_logging('Monitor')
from COMPS.Data.Simulation import SimulationState


class SimulationMonitor(object):
    """
    A class to monitor the status of simulations in the local DB.
    """

    def __init__(self, exp_id):
        logger.debug("Create a DB Monitor with exp_id=%s" % exp_id)
        self.exp_id = exp_id

    def query(self):
        logger.debug("Query the DB Monitor for Experiment %s" % self.exp_id)
        states, msgs = {}, {}
        experiment = DataStore.get_experiment(self.exp_id)

        if not experiment or not experiment.simulations:
            return states,msgs

        for sim in experiment.simulations:
            states[sim.id] = sim.status if sim.status else SimulationState.CommissionRequested
            msgs[sim.id] = sim.message if sim.message else ""
        logger.debug("States returned")
        logger.debug(dict(Counter(states.values())))
        return states, msgs


class CompsSimulationMonitor(SimulationMonitor):
    """
    A class to monitor the status of COMPS simulations.
    Note that only a single thread is spawned as the COMPS query is based on the experiment ID
    """

    def __init__(self, exp_id, suite_id, endpoint):
        super(CompsSimulationMonitor, self).__init__(exp_id)
        logger.debug("Create a COMPS Monitor with exp_id=%s, suite_id=%s, endpoint=%s" % (exp_id,suite_id,endpoint))
        self.suite_id = suite_id
        self.server_endpoint = endpoint

    @retry_function
    def query(self):
        logger.debug("Query the HPC Monitor for Experiment %s" % self.exp_id)

        COMPS_login(self.server_endpoint)
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
            id_string = str(sim.id)
            state_string = sim.state.name
            states[id_string] = state_string
            msgs[id_string] = ''

        logger.debug("States returned")
        logger.debug(json.dumps(dict(Counter(states.values())), indent=3))

        return states, msgs
