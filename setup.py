from __future__ import print_function
import ctypes
import os
import re
import shutil
import sys
from ConfigParser import ConfigParser
from collections import OrderedDict
from datetime import datetime
from distutils.version import LooseVersion
from urlparse import urlparse
from argparse import ArgumentParser, Namespace

from simtools.Utilities.General import nostdout
from simtools.Utilities.GitHub.MultiPartFile import GitHubFile
from simtools.Utilities.LocalOS import LocalOS

current_directory = os.path.dirname(os.path.abspath(__file__))
install_directory = os.path.join(current_directory, 'install')

installed_packages = dict()

# to fake out urlparse, setting netloc == 'GITHUB'
GITHUB = 'GITHUB'
GITHUB_URL_PREFIX = 'http://%s' % GITHUB

# Set the list of requirements here
# For Windows, the wheel can be provided in either tar.gz or whl format
requirements = OrderedDict([
    ('curses', {
        'platform': [LocalOS.WINDOWS],
        'version': '2.2',
        'test': '==',
        'wheel': '%s/curses-2.2-cp27-none-win_amd64.whl' % GITHUB_URL_PREFIX
    }),
    ('pyCOMPS', {
        'platform': [LocalOS.WINDOWS, LocalOS.LINUX, LocalOS.MAC],
        'version': '1.0.1',
        'test': '==',
        'wheel': '%s/pyCOMPS-1.0.1-py2.py3-none-any.whl' % GITHUB_URL_PREFIX
    }),
    ('matplotlib', {
        'platform': [LocalOS.WINDOWS, LocalOS.LINUX, LocalOS.MAC],
        'version': '1.5.3',
        'test': '>=',
        'wheel': '%s/matplotlib-1.5.3-cp27-cp27m-win_amd64.whl' % GITHUB_URL_PREFIX
    }),
    ('scipy', {
        'platform': [LocalOS.WINDOWS, LocalOS.LINUX, LocalOS.MAC],
        'version': '0.19.0',
        'test': '>=',
        'wheel': '%s/scipy-0.19.0-cp27-cp27m-win_amd64.whl' % GITHUB_URL_PREFIX
    }),
    ('pandas', {
        'platform': [LocalOS.WINDOWS, LocalOS.LINUX, LocalOS.MAC],
        'version': '0.20.2',
        'test': '>=',
        'wheel': '%s/pandas-0.20.2-cp27-cp27m-win_amd64.whl' % GITHUB_URL_PREFIX
    }),
    ('psutil', {
        'platform': [LocalOS.WINDOWS, LocalOS.LINUX, LocalOS.MAC],
        'version': '4.3.1',
        'test': '==',
        'wheel': '%s/psutil-4.3.1-cp27-cp27m-win_amd64.whl' % GITHUB_URL_PREFIX
    }),
    ('python-snappy', {
        'platform': [LocalOS.WINDOWS, LocalOS.LINUX],
        'version': '0.5',
        'test': '==',
        'wheel': '%s/python_snappy-0.5-cp27-none-win_amd64.whl' % GITHUB_URL_PREFIX
    }),
    ('seaborn', {
        'platform': [LocalOS.WINDOWS, LocalOS.LINUX, LocalOS.MAC],
        'version': '0.7.1',
        'test': '==',
        'wheel': '%s/seaborn-0.7.1-py2.py3-none-any.whl' % GITHUB_URL_PREFIX
    }),
    ('statsmodels', {
        'platform': [LocalOS.WINDOWS, LocalOS.LINUX, LocalOS.MAC],
        'version': '0.8.0',
        'test': '==',
        'wheel': '%s/statsmodels-0.8.0-cp27-cp27m-win_amd64.whl' % GITHUB_URL_PREFIX
    }),
    ('SQLAlchemy', {
        'platform': [LocalOS.WINDOWS, LocalOS.LINUX, LocalOS.MAC],
        'version': '1.1.5',
        'test': '=='
    }),
    ('npyscreen', {
        'platform': [LocalOS.WINDOWS, LocalOS.LINUX, LocalOS.MAC],
        'version': '4.10.5',
        'test': '=='
    }),
    ('fasteners', {
        'platform': [LocalOS.WINDOWS, LocalOS.LINUX, LocalOS.MAC],
        'version': '0.14.1',
        'test': '=='
    }),
    ('decorator', {
        'platform': [LocalOS.MAC],
        'version': '4.0.10',
        'test': '=='
    }),
    ('validators', {
        'platform': [LocalOS.WINDOWS, LocalOS.LINUX, LocalOS.MAC],
    }),
    ('networkx', {
        'platform': [LocalOS.WINDOWS, LocalOS.LINUX, LocalOS.MAC],
    }),
    ('patsy', {
        'platform': [LocalOS.WINDOWS, LocalOS.LINUX, LocalOS.MAC],
    }),
    ('dill', {
        'platform': [LocalOS.WINDOWS, LocalOS.LINUX, LocalOS.MAC],
    }),
    ('enum34', {
        'platform': [LocalOS.WINDOWS, LocalOS.LINUX, LocalOS.MAC],
    }),
    ('github3.py', {
        'platform': [LocalOS.WINDOWS, LocalOS.LINUX, LocalOS.MAC],
        'version': '1.0.0a4',
        'test': '>='
    }),
    ('numpy', {
        'platform': [LocalOS.WINDOWS, LocalOS.LINUX, LocalOS.MAC],
        'version': '1.13.0+mkl',
        'test': '>=',
        'wheel': '%s/numpy-1.13.0+mkl-cp27-cp27m-win_amd64.whl' % GITHUB_URL_PREFIX
    }),
])


def get_installed_packages():
    """
    Check packages in system
    """
    import pip

    # Flatten the list
    for package in pip.get_installed_distributions():
        installed_packages[package.project_name] = package.version


def download_file(url):
    """
    Download package
    """
    import urllib2

    local_file = get_local_file_path(url)

    req = urllib2.Request(url)
    resp = urllib2.urlopen(req)
    data = resp.read()
    with open(local_file, "wb") as code:
        code.write(data)

    return local_file


def get_local_file_path(url):
    # If it is local file, use it
    if os.path.exists(url):
        return url

    # Compose local file
    file_name = os.path.basename(url)
    local_file = os.path.join(install_directory, file_name)
    return local_file


def install_package(my_os, name, val, upgrade=False):
    """
    Install or upgrade package
    """
    import pip
    package_str = build_package_str(my_os, name, val)

    host, path = urlparse(package_str)[1:3]
    # It is an internet file
    if (len(host) > 0 and len(path) > 0) or host == GITHUB:
        local_file = get_local_file_path(package_str)
        if not os.path.exists(local_file):
            # Download file if it does not exist locally
            if host == GITHUB:
                dependency = GitHubFile(local_file)
                dependency.pull() # writes to local_file
            else:
                local_file = download_file(package_str)

        # Install package from local file (just downloaded or existing one)
        if upgrade:
            pip.main(['install', local_file, '--upgrade'])
        else:
            pip.main(['install', local_file])
    # Check if it is local wheel file or tar.gz file
    elif (package_str.endswith('.whl') or package_str.endswith('.tar.gz')) \
            and os.path.exists(get_local_file_path(package_str)):
        # Use local file if it exists
        if upgrade:
            pip.main(['install', get_local_file_path(package_str), '--upgrade'])
        else:
            pip.main(['install', get_local_file_path(package_str)])
    # Just package name w/o version
    else:
        if upgrade:
            pip.main(['install', package_str, '--upgrade'])
        else:
            pip.main(['install', package_str])


def test_package_g(my_os, name, val):
    """
    Case: required version > installed version
    """
    version = val.get('version', None)
    test = val.get('test', None)

    if test in ['==', '>=']:
        print("Package %s (%s) already installed with lower version. Upgrading to (%s)..." %  (name, installed_packages[name], version))
        install_package(my_os, name, val, True)
    else:
        # Usually we don't have this case.
        print ("Package %s (%s) already installed. Skipping..." % (name, installed_packages[name]))


def test_package_e(my_os, name, val):
    """
    Case: required version == installed version
    """
    test = val.get('test', None)

    if test in ['>=', '<=']:
        print ("Package %s (%s) already installed. Skipping..." % (name, installed_packages[name]))
    elif test in ['==']:
        print ("Package %s (%s) with exact version already installed. Skipping..." % (name, installed_packages[name]))
    else:
        print ("Package %s (%s) installed. Skipping..." % (name, installed_packages[name]))


def test_package_l(my_os, name, val):
    """
    Case: required version < installed version
    """
    version = val.get('version', None)

    # Usually we don't have this case.
    print ("Package %s (%s) with higher version installed but require lower version (%s). Installing..." %  (name, installed_packages[name], version))
    install_package(my_os, name, val)


def test_package(my_os, name, val):
    """
    Check installation
    """
    version = val.get('version', None)

    if name in installed_packages:
        if not version:
            print ("Package %s (%s) installed. Skipping..." % (name, installed_packages[name]))
            return

        if LooseVersion(version) > LooseVersion(installed_packages[name]):
            test_package_g(my_os, name, val)
        elif LooseVersion(version) == LooseVersion(installed_packages[name]):
            test_package_e(my_os, name, val)
        else:
            test_package_l(my_os, name, val)
    else:
        print ("Package %s not installed. Installing..." % name)
        install_package(my_os, name, val)


def build_package_str(my_os, name, val):
    """
    Build package installation string
    """
    package_str = None

    if my_os in [LocalOS.WINDOWS]:
        if val.get('wheel', None):
            package_str = val['wheel']
        elif val.get('version', None):
            # Win doesn't support >= or <=. Replace with ==
            op = val['test']
            op = re.sub('[><]', '=', op) if not op else op
            package_str = "%s%s%s" % (name, op, val['version'])
        else:
            package_str = name
    elif my_os in [LocalOS.MAC, LocalOS.LINUX]:
        if val.get('test', None) and val.get('version', None):
            package_str = "%s%s%s" % (name, val['test'], val['version'])
        else:
            package_str = "%s" % name

    return package_str


def get_requirements_by_os(my_os):
    """
    Update requirements based on OS
    """
    reqs = OrderedDict([(name, val) for (name, val) in requirements.iteritems() if my_os in val['platform']])

    # OS: Mac or Linux. No wheel needed
    if my_os in [LocalOS.MAC, LocalOS.LINUX]:
        for (name, val) in reqs.iteritems():
            if 'wheel' in val:
                val.pop('wheel')

    # OS: Linux. No version for some packages
    if my_os in [LocalOS.LINUX]:
        for name in ['numpy', 'scipy']:
            if 'version' in reqs[name]:
                reqs[name].pop('version')
            if 'test' in reqs[name]:
                reqs[name].pop('test')

    return reqs


def install_linux_pre_requisites():
    """
    Install pre-requisites for Linux
    """
    # Doing the apt-get install pre-requisites
    from subprocess import check_call, STDOUT
    pre_requisites = [
        'python-setuptools',
        'python-pip',
        'psutils',
        'build-essential',
        'python-dev',
        'libsnappy-dev',
        'ncurses-dev',
        'libfreetype6-dev',
        'python-numpy',
        'liblapack-dev',
        'python-scipy'
    ]

    supports_apt_get = False
    try:
        check_call('apt-get -h', stdout=open(os.devnull, 'wb'), stderr=STDOUT)
        supports_apt_get = True
    except OSError:
        print ("Not able to automatically install packages via apt-get.  Please meke sure the following dependencies are installed on your system:")
        print (pre_requisites)
    except:
        print ("Unexpected error checking for apt-get:", sys.exc_info()[0])
        raise

    if supports_apt_get:
        for req in pre_requisites:
            print ("Checking/Installing %s" % req)
            check_call(['apt-get', 'install', '-y', req], stdout=open(os.devnull, 'wb'), stderr=STDOUT)


def install_packages(my_os, reqs):
    """
    Install required packages
    """
    if my_os in [LocalOS.LINUX]:
        # Doing the apt-get install pre-requisites
        install_linux_pre_requisites()

    # Get the installed package to not reinstall everything
    get_installed_packages()

    # Go through the requirements
    for (name, val) in reqs.iteritems():
        test_package(my_os, name, val)

    # Add the develop by default
    sys.argv.append('develop')
    sys.argv.append('--quiet')

    from setuptools import setup, find_packages
    # Suppress the outputs except the errors
    with nostdout(stderr=True):
        setup(name='dtk-tools',
              version='0.6',
              description='Facilitating submission and analysis of simulations',
              url='https://github.com/InstituteforDiseaseModeling/dtk-tools',
              author='Edward Wenger,'
                     'Benoit Raybaud,'
                     'Daniel Klein,'
                     'Jaline Gerardin,'
                     'Milen Nikolov,'
                     'Aaron Roney,'
                     'Zhaowei Du,'
                     'Prashanth Selvaraj'
                     'Clark Kirkman IV',
              author_email='ewenger@intven.com,'
                           'braybaud@intven.com,'
                           'dklein@idmod.org,'
                           'jgerardin@intven.com,'
                           'mnikolov@intven.com,'
                           'aroney@intven.com,'
                           'zdu@intven.com,'
                           'pselvaraj@intven.com'
                           'ckirkman@intven.com',
              packages=find_packages(),
              install_requires=[],
              entry_points={
                  'console_scripts': ['calibtool = calibtool.commands:main', 'dtk = dtk.commands:main']
              },
              package_data={'': ['simtools/simtools.ini']},
              zip_safe=False)


def handle_init():
    """
    Consider user's configuration file
    """
    # Copy the default.ini into the right directory if not already present
    current_simtools = os.path.join(current_directory, 'simtools', 'simtools.ini')
    default_ini = os.path.join(install_directory, 'default.ini')
    if not os.path.exists(current_simtools):
        shutil.copyfile(default_ini, current_simtools)
    else:
        # A simtools was already present, merge the best we can
        print ("\nA previous simtools.ini configuration file is present. Attempt to auto-merge")
        merge_cp = ConfigParser()
        merge_cp.read([default_ini, current_simtools])

        # Backup copy the current
        print ("Backup copy your current simtools.ini to simtools.ini.bak")
        shutil.copy(current_simtools, current_simtools + ".bak")

        # Write the merged one
        merge_cp.write(open(current_simtools, 'w'))
        print ("Merged simtools.ini written!\n")

    # Create the EXAMPLE block for the examples
    example_simtools = os.path.join(current_directory, 'examples', 'simtools.ini')

    # Create the simtools.ini if doesnt exist. Append so if it exists, will not alter the contents
    open(example_simtools, 'a').close()

    # Check if we have the EXAMPLE block
    cp = ConfigParser()
    cp.read(example_simtools)

    if not cp.has_section('EXAMPLE'):
        # EXAMPLE section is not here -> create it
        cp.add_section('EXAMPLE')
        cp.set('EXAMPLE', 'type', 'LOCAL')
        cp.set('EXAMPLE', 'input_root', os.path.join(current_directory, 'examples', 'inputs'))
    if not cp.has_section('HPC'):
        cp.add_section('HPC')
        cp.set('HPC', 'type', 'HPC')
        cp.set('HPC', 'lib_staging_root', '$COMPS_PATH(HOME)\\braybaud\\malariaongoing')
        cp.set('HPC', 'bin_staging_root', '$COMPS_PATH(HOME)\\braybaud\\malariaongoing\\Eradication.exe')

    cp.write(open(example_simtools, 'w'))


def upgrade_pip(my_os):
    """
    Upgrade pip before install other packages
    """
    import subprocess

    if my_os in [LocalOS.MAC, LocalOS.LINUX]:
        subprocess.call("pip install -U pip", shell=True)
    elif my_os in [LocalOS.WINDOWS]:
        subprocess.call("python -m pip install --upgrade pip", shell=True)


def verify_matplotlibrc(my_os):
    """
    on MAC: make sure file matplotlibrc has content
    backend: Agg
    """
    if my_os not in [LocalOS.MAC]:
        return

    import matplotlib as mpl
    config_dir = mpl.get_configdir()
    rc_file = os.path.join(config_dir, 'matplotlibrc')

    def has_Agg(rc_file):
        with open(rc_file, "r") as f:
            for line in f:
                ok = re.match(r'^.*backend.*:.*$', line)
                if ok:
                    return True

        return False

    if os.path.exists(rc_file):
        ok = has_Agg(rc_file)
        if not ok:
            # make a backup of existing rc file
            directory = os.path.dirname(rc_file)
            backup_id = 'backup_' + re.sub('[ :.-]', '_', str(datetime.now().replace(microsecond=0)))
            shutil.copy(rc_file, os.path.join(directory, '%s_%s' % ('matplotlibrc', backup_id)))

            # append 'backend : Agg' to existing file
            with open(rc_file, "a") as f:
                f.write('\nbackend : TkAgg')
    else:
        # create a rc file
        with open(rc_file, "wb") as f:
            f.write('backend : TkAgg')

def cleanup_locks():
    """
    Deletes the lock files if they exist
    :return:
    """
    current_dir = os.path.dirname(os.path.realpath(__file__))
    setupparser_lock = os.path.join(current_dir, 'simtools','.setup_parser_init_lock')
    overseer_lock = os.path.join(current_dir, 'simtools','ExperimentManager','.overseer_check_lock')
    if os.path.exists(setupparser_lock):
        try:
            os.remove(setupparser_lock)
        except:
            print("Could not delete file: %s" % setupparser_lock)

    if os.path.exists(overseer_lock):
        try:
            os.remove(overseer_lock)
        except:
            print("Could not delete file: %s" % overseer_lock)


def main():
    # if we add any more options, do this in a separate method
    parser = ArgumentParser()
    parser.add_argument('--nopackages', action='store_false', dest='get_packages',
                        help='Do not automatically obtain disease packages (Default: obtain them).')
    args = parser.parse_args()
    # silly, but prevents conflict with install_packages method
    if '--nopackages' in sys.argv:
        sys.argv.remove('--nopackages')

    # Check OS
    my_os = LocalOS.name
    print ('os: %s' % my_os)

    # Upgrade pip before install other packages
    upgrade_pip(my_os)

    # Get OS-specific requirements
    reqs = get_requirements_by_os(my_os)

    # Install required packages
    install_packages(my_os, reqs)

    # Consider config file
    handle_init()

    # Make sure matplotlibrc file is valid
    verify_matplotlibrc(my_os)

    # Obtain the most recent disease input packages
    if args.get_packages:
        import dtk.commands
        namespace = Namespace()
        setattr(namespace, 'quiet', True)
        package_names = dtk.commands.list_packages(args=namespace, unknownArgs=None)
        for package_name in package_names:
            setattr(namespace, 'package_name', package_name)
            setattr(namespace, 'package_version', 'latest')
            dtk.commands.get_package(args=namespace, unknownArgs=None)

    cleanup_locks()

    # Success !
    print ("\n=======================================================")
    print ("| Dtk-Tools and dependencies installed successfully.  |")
    print ("=======================================================")


if __name__ == "__main__":
    # check os first
    if ctypes.sizeof(ctypes.c_voidp) != 8:
        print ("""\nFATAL ERROR: dtk-tools only supports Python 2.7 x64. Please download and install a x86-64 version of python at:
        - Windows: https://www.python.org/downloads/windows/
        - Mac OSX: https://www.python.org/downloads/mac-osx/
        - Linux: https://www.python.org/downloads/source/\n
        Installation is now exiting...""")
        exit()

    main()

