# this file contains methods for interfacing with the disease input packages github repository
import subprocess
import os

PACKAGES_GITHUB_URL = 'https://github.com/InstituteforDiseaseModeling/dtk-packages.git'

# e.g. malaria-v2.1 -> ['malaria', 'v2.1']
def parse_version(tag):
    return tag.split('-')

def construct_version(disease, ver):
    return '-'.join([disease, ver])

def get_latest_version_for_package(package_name):
    versions = get_versions_for_package(package_name)
    if len(versions) == 0:
        version = None
    else:
        version = sorted(versions)[-1]
    return version

# returns True/False if the given inputs package exists in github
def package_exists(package_name):
    packages = get_available('branch')
    return packages.__contains__(package_name)

def version_exists_for_package(version, package_name):
    available_versions = get_versions_for_package(package_name)
    return available_versions.__contains__(version)

# Find the available versions for the given disease package
def get_versions_for_package(package_name):
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

# Returns the available packages (branches) or versions of a package (tag)
# type is 'branch' or 'tag'
def get_available(type):
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
    os.system("git clone -q %s %s" % (PACKAGES_GITHUB_URL, dest))

# checks out a particular git id at the specified directory
# id is a tag or commit id
def checkout(dir, git_id):
    original_dir = os.getcwd()
    os.chdir(dir)
    cmd = "git checkout -q %s" % git_id
    os.system(cmd)
    os.chdir(original_dir)
