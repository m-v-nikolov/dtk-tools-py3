import os
import uuid

from simtools.Utilities.General import retry_function

class GitHub(object):
    """
    This class is intended to be subclassed for use. Defined subclasses go at the bottom of this file.
    """

    class BadCredentials(Exception): pass
    class AuthorizationError(Exception): pass
    class UnknownRepository(Exception): pass

    # derivative classes may redefine the following fields
    DEFAULT_REPOSITORY_NAME = None
    OWNER = 'InstituteforDiseaseModeling'
    AUTH_TOKEN_FIELD = 'github_authentication_token'
    SUPPORT_EMAIL = 'IDM-SW-Research@intven.com'
    AUTH_TOKEN = None # allows subclasses to bypass interactive login if overridden

    HEAD = 'HEAD'

    def __init__(self, repository_name=None):
        self.repository_name = repository_name or self.DEFAULT_REPOSITORY_NAME
        if not self.repository_name:
            raise Exception('repository name not supplied')
        self._repo = None
        self.owner = self.OWNER
        self.auth_token_field = self.AUTH_TOKEN_FIELD
        self.support_email = self.SUPPORT_EMAIL

    @property
    def repository(self):
        if not self._repo:
            self.login()
        if not self._repo:
            print("/!\\ WARNING /!\\ Authorization failure. You do not currently have permission to access disease packages. " \
                  "Please contact %s for assistance." % self.support_email); sys.stdout.flush()
            raise self.AuthorizationError()
        return self._repo

    def login(self):
        import github3
        # Get an authorization token first
        token = self.retrieve_token()
        self.session = github3.login(token=token)
        self._repo = self.session.repository(self.OWNER, self.repository_name)

    def retrieve_token(self):
        if self.AUTH_TOKEN:
            token = self.AUTH_TOKEN
        else:
            from simtools.DataAccess.DataStore import DataStore
            setting = DataStore.get_setting(self.auth_token_field)
            if setting:
                token = setting.value
            else:
                token = self.create_token()
        return token

    def create_token(self):
        import getpass
        import github3
        # Asks user for username/password
        user = raw_input("Please enter your GitHub username: ")
        password = getpass.getpass(prompt="Please enter your GitHub password: ")

        # Info for the GitHub token
        note = 'dtk-tools-%s' % str(uuid.uuid4())[:4]
        note_url = 'https://github.com/%s/%s' % (self.OWNER, self.repository_name)
        scopes = ['user', 'repo']

        # Authenticate the user and create the token
        try:  # user may not have permissions to use the disease package repo yet
            if len(user) == 0 or len(password) == 0:
                raise self.BadCredentials()
            auth = github3.authorize(user, password, scopes, note, note_url)
        except (github3.GitHubError, self.BadCredentials):
            print "/!\\ WARNING /!\\ Bad GitHub credentials. Cannot access disease packages. Please contact %s for assistance." \
                  % self.SUPPORT_EMAIL
            raise self.AuthorizationError()

        # Write the info to disk
        # Update the (local) mysql db with the token
        from simtools.DataAccess.DataStore import DataStore
        DataStore.save_setting(DataStore.create_setting(key=self.auth_token_field, value=auth.token))

        return auth.token

    @retry_function
    def get_directory_contents(self, directory):
        contents = self.repository.directory_contents(directory, return_as=dict)
        return contents

    def file_in_repository(self, filename):
        """
        Determines if the specified filename exists in the given repository object
        :param filename: a '/' delim filepath relative to the repository root
        :return: True/False
        """
        contents = self.get_directory_contents(os.path.dirname(filename))
        if filename in contents:
            return True
        else:
            return False

    @retry_function
    def get_file_data(self, filename):
        directory = os.path.dirname(filename)
        contents = self.get_directory_contents(directory)
        if filename in contents:
            download_url = contents[filename].download_url
            import urllib2
            try:
                req = urllib2.Request(download_url)
                resp = urllib2.urlopen(req)
                data = resp.read()
            except:
                raise Exception("Could not retrieve file: %s in repository: %s" % (filename, self.repository_name))
        else:
            data = None
        return data

    @retry_function
    def get_zip(self, tag, destination):
        """
        Obtains an archive zip of the specified git tag and names the resultant file: zip_file
        :param destination: The zip file to write
        :param tag: the git tag to retrieve a zip of
        :return: Nothing.
        """
        # make sure we get a clean copy
        if os.path.exists(destination):
            os.remove(destination)
        success = self.repository.archive('zipball', path=destination, ref=tag)
        if not success:
            raise Exception("Failed to download zip of tag: %s from repository %s ." % (tag, self.repository_name))
        return destination

#
# Derivative classes here
#

from distutils.version import LooseVersion
class DTKGitHub(GitHub):
    # this file contains methods for interfacing with the disease input packages github repository

    TEST_DISEASE_PACKAGE_NAME = 'test'
    RELEASE = 'release'

    # holds a dict of disease -> repository name mapping
    import json
    PACKAGE_MAP_FILENAME = os.path.join(os.path.dirname(__file__), 'repository_map.json')
    PACKAGE_LIST = json.loads(open(PACKAGE_MAP_FILENAME, 'r').read())

    def __init__(self, disease):
        self.disease_package_db_key = disease + '_package_version'
        if not self.PACKAGE_LIST.get(disease, None):
            raise self.UnknownRepository('No known package repository for %s' % disease)
        super(DTKGitHub, self).__init__(repository_name=self.PACKAGE_LIST[disease])

    def get_latest_version(self):
        """
            Determines the most recent inputs version for a given disease.
            :param package_name: Looks for a version of this disease/package
            :return: The most recent version string (alphabetically last version).
        """
        versions = self.get_versions()
        if len(versions) == 0:
            version = None
        else:
            version = sorted(versions)[-1]
        return version

    def version_exists(self, version):
        """
            Determines if the specified version of the given disease inputs is available.
            :param version: The version to look for.
            :return: True/False
        """
        return version in [str(v) for v in self.get_versions()]

    @retry_function
    def get_versions(self):
        """
            Returns the (sorted) input versions available for the selected disease/package.
            :param package_name: The disease/package to check.
            :return: A list of available versions.
        """
        tags = [t.name for t in self.repository.tags()]
        versions = []
        for tag in tags:
            try:
                version = self.parse_tag(tag)
            except:
                continue # ignore tags of alternate formats
            versions.append(version)
        return sorted(versions)

    @classmethod
    def get_package_list(cls):
        return sorted(cls.PACKAGE_LIST.keys())

    @classmethod
    def parse_tag(cls, tag):
        """
            Converts a disease input package version (tag name) to its package/version components.
            :param tag: A GitHub tag to parse.
            :return: A length 2 list: [PACKAGE_NAME, VERSION_STR]
        """
        str, version = tag.split('-')
        try:
            version = LooseVersion(version)
            if str != cls.RELEASE:
                raise Exception()
        except:
            raise Exception('The tag: %s is not a valid version format.' % tag)
        return version

    @classmethod
    def construct_tag(cls, ver):
        """
            Constructs a disease input package version (tag name) from package/version components.
            :param disease: The disease/package name to construct a GitHub tag from.
            :param ver: The version of the specified package/disease.
            :return: A len 2 list: PACKAGE_NAME-VERSION_STR
        """
        return '-'.join([cls.RELEASE, str(ver)])

    def get_zip(self, version, destination):
        """
        Obtains the requested disease input package & version and puts it at the desired location.
        :param package: The disease input package to obtain.
        :param version: The version of said package.
        :param dest: The directory to contain obtained inputs.
        :return: Nothing.
        """
        if version == self.HEAD:
            release_tag = self.HEAD
        else:
            release_tag = self.construct_tag(version)
        zip_file = os.path.join(destination, '%s.zip' % release_tag)
        return super(DTKGitHub, self).get_zip(tag=release_tag, destination=zip_file)

class DependencyGitHub(GitHub):
    DEFAULT_REPOSITORY_NAME = 'PythonDependencies'
    AUTH_TOKEN = '09ef3bad6e6eef13ddca6848c75ad1cd83e71051' # set token here to the default RO user
