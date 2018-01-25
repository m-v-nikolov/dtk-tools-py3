class COMPSCache:
    _simulations = {}
    _experiments = {}

    @classmethod
    def simulations(cls, sid, criteria=None, children=None):
        if criteria:
            return cls.query_simulation(sid, criteria, children)

        if sid not in cls._simulations:
            cls.load_simulation(sid, criteria, children)

        return cls._simulations[sid]

    @classmethod
    def experiments(cls, eid, criteria=None, children=None):
        if criteria:
            return cls.query_experiment(eid, criteria, children)

        if eid not in cls._experiments:
            cls.load_experiment(eid, criteria, children)

        return cls._experiments[eid]

    @classmethod
    def load_simulation(cls, sid, criteria=None, children=None):
        s = cls.query_simulation(sid, criteria, children)
        cls._simulations[sid] = s
        cls.load_experiment(s.experiment_id)

    @classmethod
    def load_experiment(cls, eid, criteria=None, children=None):
        e = cls.query_experiment(eid, criteria, children)
        cls._experiments[eid] = e

        for s in cls.get_experiment_simulations(e):
            cls._simulations[str(s.id)] = s

    @staticmethod
    def get_experiment_simulations(exp):
        return exp.get_simulations()

    @staticmethod
    def query_experiment(eid=None, criteria=None, children=None):
        from COMPS.Data import Experiment
        from COMPS.Data import QueryCriteria

        criteria = criteria or QueryCriteria()
        children = children or ["tags"]
        criteria.select_children(children)

        exp = Experiment.get(eid, query_criteria=criteria)
        return exp

    @staticmethod
    def query_simulation(sid, criteria=None, children=None):
        from COMPS.Data import Simulation
        from COMPS.Data import QueryCriteria
        if children:
            criteria = criteria or QueryCriteria()
            criteria.select_children(children)

        return Simulation.get(sid, query_criteria=criteria)
