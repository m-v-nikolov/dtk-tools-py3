import getpass
import psycopg2

from simtools.Utilities.LocalOS import LocalOS

class reg(object):
    def __init__(self, cursor, row):
        for (attr, val) in zip((d[0] for d in cursor.description), row) :
            setattr(self, attr, val)


def idm_DB_connection():
    try:
        server_name = 'ivlabsdssql01.na.corp.intven.com'
        cnxn = psycopg2.connect(host=server_name, port=5432, dbname='idm_db',
                                user=LocalOS.username, password=getpass.getpass())
    except psycopg2.Error:
        raise Exception("Failed connection to %s." % server_name)
    return cnxn
