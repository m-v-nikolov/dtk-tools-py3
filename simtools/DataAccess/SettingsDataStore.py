from simtools.DataAccess import session_scope
from simtools.DataAccess.Schema import Settings


class SettingsDataStore:
    @classmethod
    def get_setting(cls, setting):
        with session_scope() as session:
            setting = session.query(Settings).filter(Settings.key == setting).one_or_none()
            session.expunge_all()

        return setting

    @classmethod
    def save_setting(cls, setting):
        with session_scope() as session:
            session.merge(setting)

    @classmethod
    def create_setting(cls, **kwargs):
        return Settings(**kwargs)