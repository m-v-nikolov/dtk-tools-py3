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
