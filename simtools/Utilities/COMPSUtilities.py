from COMPS.Data import Experiment
from COMPS.Data import QueryCriteria
from COMPS.Data import Simulation
from COMPS.Data import Suite


def get_experiment_by_id(exp_id):
    return Experiment.get(exp_id)

def get_experiments_per_user_and_date(user, limit_date):
    limit_date_str = limit_date.strftime("%Y-%m-%d")
    return Experiment.get(query_criteria=QueryCriteria().where('owner=%s,DateCreated>%s' % (user, limit_date_str)))

def get_experiments_by_name(name, user):
    return Experiment.get(query_criteria=QueryCriteria().where(['name~%s' % name, 'owner=%s' % user]))

def sims_from_experiment(e):
    return e.get_simulations(QueryCriteria().select(['id', 'state']).select_children('hpc_jobs'))

def experiment_needs_commission(e):
    return e.get_simulations(QueryCriteria().select(['id']).where("state=Created"))

def sims_from_experiment_id(exp_id):
    return Simulation.get(query_criteria=QueryCriteria().select(['id', 'state']).where('experiment_id=%s' % exp_id))


def sims_from_suite_id(suite_id):
    exps = Experiment.get(query_criteria=QueryCriteria().where('suite_id=%s' % suite_id))
    sims = []
    for e in exps:
        sims += sims_from_experiment(e)
    return sims


def experiment_is_running(e):
    return len(e.get_simulations(query_criteria=QueryCriteria().where('state=Running')) + e.get_simulations(query_criteria=QueryCriteria().where('state=Waiting'))) != 0

def workdirs_from_simulations(sims):
    return {str(sim.id): sim.hpc_jobs[-1].working_directory for sim in sims}


def workdirs_from_experiment_id(exp_id):
    e = Experiment.get(exp_id)
    sims = sims_from_experiment(e)
    return workdirs_from_simulations(sims)


def workdirs_from_suite_id(suite_id):
    # print('Simulation working directories for SuiteId = %s' % suite_id)
    s = Suite.get(suite_id)
    exps = s.get_experiments(QueryCriteria().select('id'))
    sims = []
    for e in exps:
        sims.extend(sims_from_experiment(e))
    return workdirs_from_simulations(sims)

def delete_suite(suite_id):
    s = Suite.get(suite_id)
    try:
        s.delete()
    except Exception as e:
        print "Could not delete suite %s" % suite_id