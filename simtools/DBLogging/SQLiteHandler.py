import logging
import datetime

from simtools.DataAccess.LoggingDataStore import LoggingDataStore


class SQLiteHandler(logging.Handler):
    """
    This version sacrifices performance for thread-safety:
    Instead of using a persistent cursor, we open/close connections for each entry.
    """
    def __init__(self):
        logging.Handler.__init__(self)

    def formatDBTime(self, record):
        record.dbtime = datetime.datetime.now()

    def emit(self, record):
        # Use default formatting:
        self.format(record)
        # Set the database time up:
        self.formatDBTime(record)
        if record.exc_info:
            record.exc_text = logging._defaultFormatter.formatException(record.exc_info)
        else:
            record.exc_text = ""
        record_info = record.__dict__

        # Pass if module is built-in
        if record_info['module'] in ['init', 'pep425tags', 'SerializableEntity']: return

        # Insert log record
        record = LoggingDataStore.create_record(
            created=record_info['dbtime'],
            name=record_info['name'],
            log_level=record_info['levelno'],
            log_level_name=record_info['levelname'],
            message=str(record_info['msg']),
            # args=record_info['args'],
            module=record_info['module'],
            func_name=record_info['funcName'],
            line_no=record_info['lineno'],
            exception=record_info['exc_text'],
            #process=record_info['process'],
            #thread=record_info['thread'],
            thread_name=record_info['threadName']
        )

        LoggingDataStore.save_record(record)
