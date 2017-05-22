import threading
import timeit
from datetime import date,timedelta

from sqlalchemy import and_
from sqlalchemy import distinct

from simtools.DataAccess import  session_scope, Session_logs, engine_logs
from simtools.DBLogging.Schema import LogRecord, Timing


class LoggingDataStore:
    @classmethod
    def create_record(cls, **kwargs):
        return LogRecord(**kwargs)

    @classmethod
    def save_record(cls, record):
        with session_scope(Session_logs()) as session:
            session.add(record)

    @classmethod
    def get_records(cls, level,modules,number):
        records = None
        with session_scope(Session_logs()) as session:
            query = session.query(LogRecord)\
                .filter(and_(LogRecord.module.in_(modules), LogRecord.log_level >= level))\
                .order_by(LogRecord.created.desc()) \
                .limit(number)
            records = query.all()
            session.expunge_all()
        return reversed(records)

    @classmethod
    def get_all_modules(cls):
        modules = None
        with session_scope(Session_logs()) as session:
            modules = [module[0] for module in session.query(distinct(LogRecord.module)).all()]
            session.expunge_all()

        return modules

    @classmethod
    def log_cleanup(cls):
        try:
            limit_date = date.today() - timedelta(days=30)
            engine_logs.execute("DELETE FROM Logs WHERE created < '%s'" % limit_date)
        except Exception as e:
            print "Could not clean the logs.\n%s" % e

    @classmethod
    def get_all_records(cls):
        all_records = None
        with session_scope(Session_logs()) as session:
            all_records = session.query(LogRecord).all()
            session.expunge_all()

        return all_records

    start_times = {}
    timing_id = "Timing"
    @classmethod
    def start_timer(cls, label):
        start_time = timeit.default_timer()
        current_thread = str(threading.current_thread().ident)
        cls.start_times[current_thread+label] = start_time

    @classmethod
    def record_time(cls, label, extra_info=None):
        current_thread = str(threading.current_thread().ident)
        elapsed = timeit.default_timer() - cls.start_times[current_thread+label]
        with session_scope(Session_logs()) as session:
            session.add(Timing(elapsed_time=elapsed, label=label, timing_id=cls.timing_id, extra_info=extra_info))
        return elapsed