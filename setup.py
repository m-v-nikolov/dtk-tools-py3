from __future__ import print_function

import ctypes
import json
import operator
import os
import re
import shutil
import sys
from collections import OrderedDict
from copy import deepcopy
from datetime import datetime
from distutils.version import LooseVersion
from enum import Enum
from urllib.request import Request, urlopen

import pip

from simtools.Utilities.General import timestamp_filename
from simtools.Utilities.GitHub.MultiPartFile import GitHubFile
from simtools.Utilities.LocalOS import LocalOS

current_directory = os.path.dirname(os.path.abspath(__file__))
install_directory = os.path.join(current_directory, 'install')

# Force writing a new simtools
force_new_simtools = False

# Force a new database ?
force_new_db = False

# This lets us guarantee a consistent time to be used for timestamped backup files
this_time = datetime.utcnow()

# to fake out urlparse, setting netloc == 'GITHUB'
GITHUB = 'GITHUB'
GITHUB_URL_PREFIX = 'http://%s' % GITHUB

# Get the installed packages on the system
installed_packages = {package.project_name: package.version for package in pip.get_installed_distributions()}

# Load the list of requirements
requirements = json.load(open('requirements.json', 'r'), object_pairs_hook=OrderedDict)

# Prepare the operators
operators = {">": operator.gt, ">=": operator.ge, "<": operator.lt, "<=": operator.le, "==": operator.eq}


class PackageStatus(Enum):
    MISSING = 0
    VALID = 1
    WRONGVERSION = 2


class DownloadMethod(Enum):
    GITHUB = 'GITHUB'
    DIRECT = 'DIRECT'


def download_wheel(wheel, method=DownloadMethod.GITHUB):
    if method == DownloadMethod.GITHUB:
        dependency = GitHubFile(wheel)
        dependency.destination_directory = install_directory
        dependency.pull()
    elif method == DownloadMethod.DIRECT:
        req = Request(wheel)
        resp = urlopen(req)
        data = resp.read()
        with open(os.path.join(install_directory, os.path.basename(wheel)), "wb") as code:
            code.write(data)
    return os.path.join(install_directory, os.path.basename(wheel))


def install_package(package, version=None, wheel=None, upgrade=False, method=DownloadMethod.GITHUB):
    # A wheel is present => easy just install it
    if wheel:
        install_str = download_wheel(wheel, method)
    else:
        # No wheel, we need to construct the string for pip
        install_str = package
        if version:
            install_str += "=={}".format(version)

    # Handle the upgrade by forcing the reinstall
    if upgrade:
        pip.main(['install', install_str, '-I'])
    else:
        pip.main(['install', install_str])


def test_package(package, version, test):
    """
    Test if a package is present and with the correct version installed.
    :param package: Package name
    :param version: Needed version
    :param test: can be >= == or <=
    :param extra: used to store extra info
    :return: PackageStatus (MISSING, VALID, WRONGVERSION)
    """
    # The package is not present -> Missing
    if package not in installed_packages:
        return PackageStatus.MISSING

    # The package is in the installed packages
    # The package has no particular version requirement -> all good
    if not version:
        return PackageStatus.VALID

    # The version is required, test if correct
    operator = operators[test]
    if not operator(LooseVersion(installed_packages[package]), LooseVersion(version)):
        return PackageStatus.WRONGVERSION

    # If we made it here, we have the correct package/version
    return PackageStatus.VALID


def get_requirements_by_os():
    """
    Update requirements based on OS
    """
    reqs = OrderedDict()

    for name, val in requirements.items():
        # If no platform specified or the os is in the platforms, add it
        if not val or 'platform' not in val or LocalOS.name in val['platform']:
            # OS: Mac or Linux. No wheel needed
            if LocalOS.name in (LocalOS.MAC, LocalOS.LINUX) and 'wheel' in val:
                val.pop('wheel')

            # OS: Linux. No version for some packages
            if LocalOS.name == LocalOS.LINUX and name in ('numpy', 'scipy'):
                if 'version' in val: val.pop('version')
                if 'test' in val: val.pop('test')

            reqs[name] = val

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


def install_packages(reqs):
    """
    Install required packages
    """
    if LocalOS.name == LocalOS.LINUX:
        # Doing the apt-get install pre-requisites
        install_linux_pre_requisites()

    # Go through the requirements
    accept_all = False
    deny_all = False
    for name, val in reqs.items():
        print("\n--- {} ---".format(name))

        val = val or {}
        version = val.get('version', None)
        test = val.get('test', '>=')
        wheel = val.get('wheel', None)
        method = DownloadMethod(val.get('method')) if 'method' in val else DownloadMethod.GITHUB
        result = test_package(name, version, test)

        # Valid package -> just display info
        if result == PackageStatus.VALID:
            print("Package {} installed and with correct version.".format(name))

        # Missing -> install
        elif result == PackageStatus.MISSING:
            print("Package {} is missing. Installing...".format(name))
            install_package(name, version, wheel, method=method)

        # Wrong version -> Prompt user
        elif result == PackageStatus.WRONGVERSION:
            current_v = installed_packages[name]
            print("Package {} is installed with version {}, but we recommend {}.".format(name, current_v, version))
            if deny_all:
                user_input = 'N'
            elif accept_all:
                user_input = 'Y'
            else:
                user_input = None

            while user_input not in ('Y', 'N', 'A', 'L'):
                user_input = input('Would you like to install the recommended version over your system version? [Y]es/[N]o/Yes to [A]ll/No to a[L]l : ').upper()
            if user_input == 'Y' or user_input == 'A':
                install_package(name, version, wheel, upgrade=True, method=method)
            else:
                print("Keeping system package {} (v. {})".format(name, current_v))

            if user_input == 'A':
                accept_all = True
            if user_input == 'L':
                deny_all = True

        print("---")

    # Add the develop by default
    sys.argv.append('develop')
    # sys.argv.append('--quiet')

    from setuptools import setup, find_packages

    setup(name='dtk-tools',
          version='1.0b3',
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
    from simtools.Utilities.ConfigObj import ConfigObj
    # Copy the default.ini into the right directory if not already present
    current_simtools = os.path.join(current_directory, 'simtools', 'simtools.ini')
    default_ini = os.path.join(install_directory, 'default.ini')
    default_config = ConfigObj(default_ini, write_empty_values=True)

    # Set some things in the default CP
    default_eradication = os.path.join(current_directory, 'examples', 'inputs', 'Eradication.exe')
    default_inputs = os.path.join(current_directory, 'examples', 'inputs')
    default_dlls = os.path.join(current_directory, 'examples', 'inputs', 'dlls')
    default_config['LOCAL']['exe_path'] = default_eradication
    default_config['LOCAL']['input_root'] = default_inputs
    default_config['LOCAL']['dll_root'] = default_dlls
    default_config['HPC']['input_root'] = default_inputs
    default_config["HPC"]["base_collection_id_input"] = ''

    if not os.path.exists(current_simtools):
        default_config.write(open(current_simtools, 'w'))
    else:
        print("\nA previous simtools.ini global configuration file is present.")

        # Backup copy the current
        dest_filename = timestamp_filename(filename=current_simtools, time=this_time)
        print("simtools.ini already exists: (%s) -> backing up to: %s" % (current_simtools, dest_filename))
        shutil.move(current_simtools, dest_filename)

        # Write new one
        print("Writing new simtools.ini")
        default_config.write(open(current_simtools, 'wb'))

    # ALso write the default_cp in the examples
    example_simtools = os.path.join(current_directory, 'examples', 'simtools.ini')
    am_examples_simtools = os.path.join(current_directory, 'examples', 'AssetManagement', 'simtools.ini')

    if os.path.exists(example_simtools):
        dest_filename = timestamp_filename(filename=example_simtools, time=this_time)
        print("Example simtools.ini already exists: (%s) -> backing up to: %s" % (example_simtools, dest_filename))
        shutil.move(example_simtools, dest_filename)

    # Smoe specific examples modifications
    example_config = deepcopy(default_config)
    example_config['HPC']['exe_path'] = default_eradication
    example_config['HPC']['dll_root'] = default_dlls
    example_config['HPC']['base_collection_id_exe'] = ''
    example_config['HPC']['base_collection_id_dll'] = ''
    example_config.write(open(example_simtools, 'wb'))

    if os.path.exists(am_examples_simtools):
        dest_filename = timestamp_filename(filename=am_examples_simtools, time=this_time)
        print("Example simtools.ini already exists: (%s) -> backing up to: %s" % (am_examples_simtools, dest_filename))
        shutil.move(am_examples_simtools, dest_filename)

    # Remove LOCAL section for the AM simtools.ini
    del default_config["LOCAL"]
    default_config.write(open(am_examples_simtools, 'wb'))


def upgrade_pip():
    """
    Upgrade pip before install other packages
    """
    import subprocess

    if LocalOS.name in (LocalOS.MAC, LocalOS.LINUX):
        subprocess.call("pip install -U pip", shell=True)
    elif LocalOS.name == LocalOS.WINDOWS:
        subprocess.call("python -m pip install --upgrade pip", shell=True)


def verify_matplotlibrc():
    """
    on MAC: make sure file matplotlibrc has content
    backend: Agg
    """
    if LocalOS.name not in [LocalOS.MAC]:
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


def backup_db():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    db_path = os.path.join(current_dir, 'simtools', 'DataAccess', 'db.sqlite')
    if os.path.exists(db_path):
        dest_filename = timestamp_filename(filename=db_path, time=this_time)
        print("Creating a new local database. Backing up existing one to: %s" % dest_filename)
        shutil.move(db_path, dest_filename)


def main():
    # Upgrade pip before install other packages
    upgrade_pip()

    # Get OS-specific requirements
    reqs = get_requirements_by_os()

    # Install required packages
    install_packages(reqs)

    # Consider config file
    if force_new_simtools: handle_init()

    # Create new db
    if force_new_db: backup_db()

    # Make sure matplotlibrc file is valid
    verify_matplotlibrc()

    cleanup_locks()

    # Success !
    print ("\n=======================================================")
    print ("| Dtk-Tools and dependencies installed successfully.  |")
    print ("=======================================================")


if __name__ == "__main__":
    # check os first
    if ctypes.sizeof(ctypes.c_voidp) != 8 or sys.version_info < (3,6):
        print("""\nFATAL ERROR: dtk-tools only supports Python 3.6 x64 and above.\n
         Please download and install a x86-64 version of python at:\n
        - Windows: https://www.python.org/downloads/windows/
        - Mac OSX: https://www.python.org/downloads/mac-osx/
        - Linux: https://www.python.org/downloads/source/\n
        Installation is now exiting...""")
        exit()

    main()
