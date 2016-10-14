import os
from contextlib import contextmanager

from simtools.utils import init_logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

current_dir = os.path.dirname(os.path.realpath(__file__))

engine = create_engine('sqlite:///%s/db.sqlite' % current_dir, echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()

@contextmanager
def session_scope(session=None):
    """Provide a transactional scope around a series of operations."""
    session = Session() if not session else session
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


logger = init_logging('DataAccess')