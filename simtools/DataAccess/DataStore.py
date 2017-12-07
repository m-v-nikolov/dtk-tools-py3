import datetime

from simtools.DataAccess.BatchDataStore import BatchDataStore
from simtools.DataAccess.ExperimentDataStore import ExperimentDataStore
from simtools.DataAccess.SettingsDataStore import SettingsDataStore
from simtools.DataAccess.SimulationDataStore import SimulationDataStore
from simtools.Utilities.General import init_logging

logger = init_logging('DataAccess')

def batch(iterable, n=1):
    """
    Batch an iterable passed as argument into lists of n elements.

    Examples:
        batch([1,2,2,3,4,5,6],2) returns [[1,2],[2,3],[4,5],[6]]

    Args:
        iterable: The iterable to split
        n: split in lists of n elements

    Returns: List of lists of n elements
    """
    logger.debug('batch function - %s in %s elements' % (iterable, n))

    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]


class DataStore(SimulationDataStore, ExperimentDataStore, SettingsDataStore, BatchDataStore):
    """
    Class holding static methods to abstract the access to the database.
    """

    @classmethod
    def list_leftover(cls, suite_ids, exp_ids):
        """
        List those experiments which are associated with suite_id and not in exp_ids
        suite_ids: list of suite ids
        exp_ids: list of experiment ids
        """
        exp_list = cls.get_experiments_by_suite(suite_ids)
        exp_list_ids = [exp.exp_id for exp in exp_list]

        # Calculate orphans
        exp_orphan_ids = list(set(exp_list_ids) - set(exp_ids))
        exp_orphan_list = [exp for exp in exp_list if exp.exp_id in exp_orphan_ids]

        return exp_orphan_list

