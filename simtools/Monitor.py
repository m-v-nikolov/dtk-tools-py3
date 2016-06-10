import json
import logging

logger = logging.getLogger(__name__)

class SimulationMonitor(object):
    """
    A class to monitor the status of local simulation.
    Threads are spawned to query each simulation in parallel.
    """

    def __init__(self, exp_data, setup):
        self.exp_data = exp_data

    def query(self):
        states, msgs = {}, {}
        for sim_id, sim in self.exp_data['sims'].items():
            states[sim_id] = sim["status"] if "status" in sim else "Waiting"
            msgs[sim_id] = sim["message"] if "message" in sim else ""
        return states, msgs


class CompsSimulationMonitor(SimulationMonitor):
    """
    A class to monitor the status of COMPS simulations.
    Note that only a single thread is spawned as the COMPS query is based on the experiment ID
    """

    def __init__(self, exp_data, setup):
        self.exp_data = exp_data
        self.server_endpoint = setup.get('server_endpoint')

    def query(self):
        from COMPS import Client
        from COMPS.Data import Experiment, Suite, QueryCriteria

        Client.Login(self.server_endpoint)

        def sims_from_experiment(e):
            #logger.info('Monitoring simulations for ExperimentId = %s', e.getId().toString())
            return e.GetSimulations(QueryCriteria().Select('Id,SimulationState')).toArray()

        def sims_from_experiment_id(exp_id):
            e = Experiment.GetById(exp_id)
            return sims_from_experiment(e)

        def sims_from_suite_id(suite_id):
            logger.info('Monitoring simulations for SuiteId = %s', suite_id)
            s = Suite.GetById(suite_id)
            exps = s.GetExperiments(QueryCriteria().Select('Id')).toArray()
            sims = []
            for e in exps:
                sims += sims_from_experiment(e)
            return sims

        if 'suite_id' in self.exp_data:
            suite_id = self.exp_data['suite_id']
            sims = sims_from_suite_id(suite_id)
        elif 'exp_id' in self.exp_data:
            exp_id = self.exp_data['exp_id']
            sims = sims_from_experiment_id(exp_id)
        else:
            raise Exception('Unable to monitor COMPS simulations as metadata contains no Suite or Experiment ID:\n%s' % json.dumps(self.exp_data, indent=4))

        states, msgs = {}, {}
        for sim in sims:
            id_string = sim.getId().toString()
            states[id_string] = sim.getState().toString()
            msgs[id_string] = ''

        return states, msgs
