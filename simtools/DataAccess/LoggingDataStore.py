from datetime import date,timedelta

from sqlalchemy import and_
from sqlalchemy import distinct

from simtools.DataAccess import  session_scope, Session_logs
from simtools.Logging.Schema import LogRecord


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
                .limit(number)
            records = query.all()
            session.expunge_all()
        return records

    @classmethod
    def get_all_modules(cls):
        modules = None
        with session_scope(Session_logs()) as session:
            modules = [module[0] for module in session.query(distinct(LogRecord.module)).all()]
            session.expunge_all()

        return modules

    @classmethod
    def cleanup(cls):
        try:
            with session_scope(Session_logs()) as session:
                session.query(LogRecord).filter(LogRecord.created < date.today() - timedelta(days=30)).delete()
        except Exception as e:
            print "Could not clean the logs.\n%s" % e

    @classmethod
    def get_all_records(cls):
        all_records = None
        with session_scope(Session_logs()) as session:
            all_records = session.query(LogRecord).all()
            session.expunge_all()

        return all_records