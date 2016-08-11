import json
import logging

from simtools.DataAccess import Session, engine, session_scope
from simtools.DataAccess.Schema import Base, Experiment, Simulation

logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def dumper(obj):
    try:
        return obj.toJSON()
    except:
        return obj.__dict__

class DataStore:
    def __init__(self):
        Base.metadata.create_all(engine)

    def cache_experiment_data(self, experiment_data, verbose=True):
        if verbose:
            logger.info('Saving meta-data for experiment:')
            logger.info(json.dumps(experiment_data, indent=3, default=dumper, sort_keys=True))

        experiment = Experiment(**experiment_data)
        with session_scope() as session:
            session.merge(experiment)


    def create_simulation(self, id, tags):
        return Simulation(id=id, tags=tags)

