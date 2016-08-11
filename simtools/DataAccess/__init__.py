import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

current_dir = os.path.dirname(os.path.realpath(__file__))

engine = create_engine('sqlite:///%s/db.sqlite' % current_dir, echo=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()