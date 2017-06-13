import github3
import os
import uuid

from simtools.DataAccess.DataStore import DataStore

class GitHub(object):
    """
    This class is intended to be subclassed for use. Defined subclasses go at the bottom of this file.
    """

    class BadCredentials(Exception): pass
    class AuthorizationError(Exception): pass

    # derivative classes must define the following fields
    REPOSITORY = None
    LOGIN_REPOSITORY = None

    # derivative classes may redefine the following fields
    OWNER = 'InstituteforDiseaseModeling'
    AUTH_TOKEN_FIELD = 'github_authentication_token'
    SUPPORT_EMAIL = 'IDM-SW-Research@intven.com'
    AUTH_TOKEN = None # allows subclasses to bypass interactive login if overridden

    @classmethod
    def repository(cls):
        if not hasattr(cls, 'repo'):
            cls.login()
        if not cls.repo:
            print "/!\\ WARNING /!\\ Authorization failure. You do not currently have permission to access disease packages. " \
                  "Please contact %s for assistance." % cls.SUPPORT_EMAIL
            raise cls.AuthorizationError()
        return cls.repo

    @classmethod
    def login(cls):
        # Get an authorization token first
        token = cls.retrieve_token()
        cls.session = github3.login(token=token)
        cls.repo = cls.session.repository(cls.OWNER, cls.REPOSITORY)

    @classmethod
    def retrieve_token(cls):
        if cls.AUTH_TOKEN:
            token = cls.AUTH_TOKEN
        else:
            setting = DataStore.get_setting(cls.AUTH_TOKEN_FIELD)
            if setting:
                token = setting.value
            else:
                token = cls.create_token()
        return token

    @classmethod
    def create_token(cls):
        import getpass
        # Asks user for username/password
        user = raw_input("Please enter your GitHub username: ")
        password = getpass.getpass(prompt="Please enter your GitHub password: ")

        # Info for the GitHub token
        note = 'dtk-tools-%s' % str(uuid.uuid4())[:4]
        note_url = 'https://github.com/%s/%s' % (cls.OWNER, cls.LOGIN_REPOSITORY)
        scopes = ['user', 'repo']

        # Authenticate the user and create the token
        try:  # user may not have permissions to use the disease package repo yet
            if len(user) == 0 or len(password) == 0:
                raise cls.BadCredentials()
            auth = github3.authorize(user, password, scopes, note, note_url)
        except (github3.GitHubError, cls.BadCredentials):
            print "/!\\ WARNING /!\\ Bad GitHub credentials. Cannot access disease packages. Please contact %s for assistance." \
                  % cls.SUPPORT_EMAIL
            raise cls.AuthorizationError()

        # Write the info to disk
        # Update the (local) mysql db with the token
        DataStore.save_setting(DataStore.create_setting(key=cls.AUTH_TOKEN_FIELD, value=auth.token))

        return auth.token

    @classmethod
    def get_directory_contents(cls, directory):
        contents = cls.repository().directory_contents(directory, return_as=dict)
        return contents

    @classmethod
    def file_in_repository(cls, filename):
        """
        Determines if the specified filename exists in the given repository object
        :param filename: a '/' delim filepath relative to the repository root
        :return: True/False
        """
        contents = cls.get_directory_contents(os.path.dirname(filename))
        if filename in contents:
            return True
        else:
            return False

    @classmethod
    def get_file_data(cls, filename):
        directory = os.path.dirname(filename)
        contents = cls.get_directory_contents(directory)
        if filename in contents:
            download_url = contents[filename].download_url
            import urllib2
            try:
                req = urllib2.Request(download_url)
                resp = urllib2.urlopen(req)
                data = resp.read()
                #            with open(local_filename, 'wb') as local_file:
                #                local_file.write(data)
            except:
                raise Exception("Could not retrieve file: %s in repository: %s" % (filename, cls.repository().name))
        else:
            data = None  # raise Exception("Requested file: %s does not exist in repository: %s" % (filename, cls.repository().name))
        return data

#
# Derivative classes here
#

class DTKGitHub(GitHub):
    REPOSITORY = 'dtk-packages'
    LOGIN_REPOSITORY = 'dtk-tools'

class DependencyGitHub(GitHub):
    REPOSITORY = 'PythonDependencies'
    LOGIN_REPOSITORY = 'PythonDependencies'
    AUTH_TOKEN = None # set token here to the default RO user