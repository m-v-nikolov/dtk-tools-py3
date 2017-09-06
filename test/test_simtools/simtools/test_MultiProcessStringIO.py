import os
import pandas as pd
import unittest
from multiprocessing.pool import ThreadPool, Pool, Process
from multiprocessing import Queue
from simtools.MultiProcessStringIO import MultiProcessStringIO, NotRegistered, AlreadyRegistered


def read_mpsio(mpsio, results):
    mpsio.register()
    print('*** My pid: %s\nregistered pids: %s\nlock: %s' % (os.getpid(), mpsio._registered_processes, hex(id(mpsio._lock))))
    # print(dir(mpsio._lock))
    value = mpsio.read(n=2)
    value += mpsio.read()
    results.put(value)

class TestMultiProcessStringIO(unittest.TestCase):

    def setUp(self):
        self.test_string = 'a,b,c\n2,4,6'
        self.pd_test_keys = self.test_string.split('\n')[0].split(',')
        self.expected_value = {
            'read': 'a,b,c\n2,4,6',
            'readline': 'a,b,c\n',
            'readlines': ['a,b,c\n','2,4,6'],
        }
        self.mpsio = MultiProcessStringIO(self.test_string)
        self.mpsio.register()

        ## because doing this inside a test case doesn't spawn new pids via os.getpid() ...
        #self.processes = [Process(target=self.read_mpsio, args=()) for i in range(100)]

    def tearDown(self):
        pass
        # self.mpsio.unregister()

    def test_register_and_unregister(self):
        self.assertTrue(os.getpid() in self.mpsio._registered_processes)
        self.mpsio.unregister()
        self.assertTrue(os.getpid() not in self.mpsio._registered_processes)

        self.assertRaises(NotRegistered, self.mpsio.read)

        self.mpsio.register()
        self.assertRaises(AlreadyRegistered, self.mpsio.register)

    def test_initial_read_index_is_0(self):
        self.assertEqual(self.mpsio._read_positions[os.getpid()], 0)

    def test_read(self):
        self.assertEqual(self.mpsio.read(), self.expected_value['read'])

    def test_readline(self):
        self.assertEqual(self.mpsio.readline(), self.expected_value['readline'])

    def test_readlines(self):
        self.assertEqual(self.mpsio.readlines(), self.expected_value['readlines'])

    def test_seek(self):
        self.mpsio.seek(pos=2)
        self.assertEqual(self.mpsio.read(), self.expected_value['read'][2:])
        self.mpsio.seek(pos=0)
        self.assertEqual(self.mpsio.read(), self.expected_value['read'])

    # single process reading
    def test_pandas_read_csv(self):
        df = pd.read_csv(self.mpsio)

        # key check
        self.assertEqual(sorted(df.keys()), sorted(self.pd_test_keys))

        # exact data checks
        self.assertEqual(len(df[df.keys()[0]]), 1)
        self.assertEqual(df['a'][0], 2)
        self.assertEqual(df['b'][0], 4)
        self.assertEqual(df['c'][0], 6)

    def test_highly_parallel_read_access(self):
        pool = [] # Process
        # pool = Pool(processes=4) # Pool

        results = Queue() # Process
        # results = [] # Pool

        for i in range(10):
            # Process() approach
            pool.append(Process(target=read_mpsio, args=(self.mpsio, results)))
            # Pool approach
            # results.append(pool.apply_async(read_mpsio, args=(self.mpsio,)))

        # Process() approach
        map(lambda x: x.start(), pool)
        map(lambda x: x.join(), pool)
        results_hash = {}
        while not results.empty():
            results_hash[results.get()] = True
        unique_results = results_hash.keys()

        # Pool approach
        # pool.close()
        # pool.join()
        # results = [result.get() for result in results]
        # unique_results = list(set(results))

        print('Unique results: %s' % unique_results)

        self.assertEqual(len(unique_results), 1)
        self.assertEqual(unique_results[0], self.expected_value['read'])

if __name__ == '__main__':
    unittest.main()
