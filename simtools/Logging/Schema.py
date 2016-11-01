import os

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String

from simtools.DataAccess import Base_logs, engine_logs


class LogRecord(Base_logs):
    __tablename__ = "Logs"
    id = Column(Integer, primary_key=True)
    created = Column(DateTime(timezone=True), index=True)
    name = Column(String, index=True)
    log_level = Column(Integer, index=True)
    log_level_name = Column(String)
    message = Column(String)
    #args = Column(PickleType(pickler=json))
    module = Column(String)
    func_name = Column(String)
    line_no = Column(Integer)
    exception = Column(String)
    #process = Column(Integer)
    #thread = Column(String)
    thread_name = Column(String)
    cwd = Column(String, default=os.getcwd())

    def __repr__(self):
        return "%s [%s] [%s] %s" % (self.created.strftime("%m/%d %H:%M:%S"), self.log_level_name, self.module, self.message)

Base_logs.metadata.create_all(engine_logs)
