import unittest
from multiprocessing import JoinableQueue, Queue

from simtools.DataAccess.Schema import Simulation
from simtools.OutputParser.OutputParserWorker import OutputParserWorker


class TestSimulationAssets(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_worker_process(self):
        simulations = JoinableQueue()
        results = Queue()
        num_processes = 4
        num_sims = 10

        # Create the workers
        workers = [OutputParserWorker(simulations, results) for _ in range(num_processes)]

        # Start the workers
        for w in workers:
            w.start()

        # Add some sims
        for i in range(num_sims):
            simulations.put(Simulation(id=i))

        # Add poison
        for i in range(num_processes):
            simulations.put(None)

        # Join the queue
        simulations.join()

        while num_sims:
            result = results.get()
            print('Result:', result)
            num_sims -= 1




