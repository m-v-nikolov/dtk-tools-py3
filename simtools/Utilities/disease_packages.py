# this file contains methods for interfacing with the disease input packages github repository
import subprocess
import os

PACKAGES_GITHUB_URL = 'https://github.com/InstituteforDiseaseModeling/dtk-packages.git'

def parse_version(tag):
    """
        Converts a disease input package version (tag name) to its package/version components.
        :param tag: A GitHub tag to parse.
        :return: A length 2 list: [PACKAGE_NAME, VERSION_STR]
    """
    return tag.split('-')

def construct_version(disease, ver):
    """
            Constructs a disease input package version (tag name) from package/version components.
            :param disease: The disease/package name to construct a GitHub tag from.
            :param ver: The version of the specified package/disease.
            :return: A len 2 list: PACKAGE_NAME-VERSION_STR
        """
    return '-'.join([disease, ver])

def get_latest_version_for_package(package_name):
    """
        Determines the most recent inputs version for a given disease.
        :param package_name: Looks for a version of this disease/package
        :return: The most recent version string (alphabetically last version).
    """
    versions = get_versions_for_package(package_name)
    if len(versions) == 0:
        version = None
    else:
        version = sorted(versions)[-1]
    return version

# returns True/False if the given inputs package exists in github
def package_exists(package_name):
    """
        Determines if the specified disease inputs package is available, any version.
        :param package_name: This is the disease/package checked.
        :return: True/False
    """
    return packages.__contains__(package_name)

def version_exists_for_package(version, package_name):
    """
        Determines if the specified version of the given disease inputs is available.
        :param version: The version to look for.
        :param package_name: The disease/package to check.
        :return: True/False
    """
    available_versions = get_versions_for_package(package_name)
    return available_versions.__contains__(version)

def get_versions_for_package(package_name):
    """
        Returns the input versions available for the selected disease/package.
        :param package_name: The disease/package to check.
        :return: A list of available versions.
    """
    tags = get_available('tag')
    versions = []
    for tag in tags:
        try:
            disease, version = parse_version(tag)
        except:
            continue  # ignore tags of alternate formats
        if disease == package_name:
            versions.append(version)
    return versions

def get_available(type):
    """
        Returns a list of all existing disease input packages (branches) or input versions (tags).
        :param type: Determines if branches or tags are listed. Pass 'branch' or 'tag'.
        :return: A list of available input packages or versions.
        :raises: Exception if type is not recognized.
    """
    if type == 'branch':
        flag = '--heads'
    elif type == 'tag':
        flag = '--tags'
    else:
        raise Exception('No such git type: %s . Must be branch or tag.' % type)
    cmd = "git ls-remote %s %s" % (flag, PACKAGES_GITHUB_URL)
    output = subprocess.check_output(cmd)
    items = output.split('\n')[0:-1]  # -1 means ignore trailing '' item
    items = [i.split('\t')[-1] for i in items] # drop leading git commit id
    results = [i.split('/')[-1] for i in items] # drop leading pathing in branch/tag names
    if type == 'branch':
        results.remove('master') # this isn't really something available for use :)
    return results

def clone(dest):
    """
        Creates a copy of the input packages repository.
        :param dest: This will be the new copy of the repository.
        :return: Nothing
    """
    os.system("git clone -q %s %s" % (PACKAGES_GITHUB_URL, dest))

def checkout(dir, git_id):
    """
        Checks out a specified git id (tag or commit) at the specified cloned directory.
        :param dir: The cloned directory to perform the checkout in.
        :param git_id: The tag or commit to checkout.
        :return: Nothing
    """
    original_dir = os.getcwd()
    os.chdir(dir)
    cmd = "git checkout -q %s" % git_id
    os.system(cmd)
    os.chdir(original_dir)
