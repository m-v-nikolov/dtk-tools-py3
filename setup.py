import ctypes
import re
import os
import platform
import shutil
import sys
from collections import OrderedDict
from urlparse import urlparse
from ConfigParser import ConfigParser
from distutils.version import LooseVersion
from simtools.utils import nostdout

current_directory = os.path.dirname(os.path.abspath(__file__))
install_directory = os.path.join(current_directory, 'install')

installed_packages = dict()

# Set the list of requirements here
# For Windows, the wheel can be provided in either tar.gz or whl format
requirements = {
    'curses': {
        'platform': ['win'],
        'version': '2.2',
        'test': '==',
        'wheel': 'https://institutefordiseasemodeling.github.io/PythonDependencies/curses-2.2-cp27-none-win_amd64.whl'
    },
    'numpy': {
        'platform': ['win', 'lin', 'mac'],
        'version': '1.11.2rc1+mkl',
        'test': '>=',
        'wheel': 'https://institutefordiseasemodeling.github.io/PythonDependencies/numpy-1.11.2rc1%2Bmkl-cp27-cp27m-win_amd64.whl'
    },
    'scipy': {
        'platform': ['win', 'lin', 'mac'],
        'version': '0.18.1',
        'test': '==',
        'wheel': 'https://institutefordiseasemodeling.github.io/PythonDependencies/scipy-0.18.1-cp27-cp27m-win_amd64.whl'
    },
    'matplotlib': {
        'platform': ['win', 'lin', 'mac'],
        'version': '1.5.3',
        'test': '>=',
        'wheel': 'https://institutefordiseasemodeling.github.io/PythonDependencies/matplotlib-1.5.3-cp27-cp27m-win_amd64.whl'
    },
    'pandas': {
        'platform': ['win', 'lin', 'mac'],
        'version': '0.19.2',
        'test': '==',
        'wheel': 'https://institutefordiseasemodeling.github.io/PythonDependencies/pandas-0.19.2-cp27-cp27m-win_amd64.whl'
    },
    'psutil': {
        'platform': ['win', 'lin', 'mac'],
        'version': '4.3.1',
        'test': '==',
        'wheel': 'https://institutefordiseasemodeling.github.io/PythonDependencies/psutil-4.3.1-cp27-cp27m-win_amd64.whl'
    },
    'python-snappy': {
        'platform': ['win', 'lin'],
        'version': '0.5',
        'test': '==',
        'wheel': 'https://institutefordiseasemodeling.github.io/PythonDependencies/python_snappy-0.5-cp27-none-win_amd64.whl'
    },
    'seaborn': {
        'platform': ['win', 'lin', 'mac'],
        'version': '0.7.1',
        'test': '==',
        'wheel': 'https://institutefordiseasemodeling.github.io/PythonDependencies/seaborn-0.7.1-py2.py3-none-any.whl'
    },
    'statsmodels': {
        'platform': ['win', 'lin', 'mac'],
        'version': '0.6.1',
        'test': '==',
        'wheel': 'https://institutefordiseasemodeling.github.io/PythonDependencies/statsmodels-0.6.1-cp27-none-win_amd64.whl'
    },
    'SQLAlchemy': {
        'platform': ['win', 'lin', 'mac'],
        'version': '1.1.0b3',
        'test': '=='
    },
    'npyscreen': {
        'platform': ['win', 'lin', 'mac'],
        'version': '4.10.5',
        'test': '=='
    },
    'decorator': {
        'platform': ['mac'],
        'version': '4.0.10',
        'test': '=='
    },
    'validators': {
        'platform': ['win', 'lin', 'mac'],
    },
    'networkx': {
        'platform': ['win', 'lin', 'mac'],
    },
    'dill': {
        'platform': ['win', 'lin', 'mac'],
    }
}


# Installation orders are required for some packages
order_requirements = ['curses', 'numpy',  'scipy', 'matplotlib']


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
    if len(host) > 0 and len(path) > 0:
        if os.path.exists(get_local_file_path(package_str)):
            # Use local file if it exists
            local_file = get_local_file_path(package_str)
        else:
            # Download file first
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
        print "Package %s (%s) already installed with lower version. Upgrading to (%s)..." % \
              (name, installed_packages[name], version)
        install_package(my_os, name, val, True)
    else:
        # Usually we don't have this case.
        print "Package %s (%s) already installed. Skipping..." % (name, installed_packages[name])


def test_package_e(my_os, name, val):
    """
    Case: required version == installed version
    """
    test = val.get('test', None)

    if test in ['>=', '<=']:
        print "Package %s (%s) already installed. Skipping..." % (name, installed_packages[name])
    elif test in ['==']:
        print "Package %s (%s) with exact version already installed. Skipping..." % \
              (name, installed_packages[name])
    else:
        print "Package %s (%s) installed. Skipping..." % (name, installed_packages[name])


def test_package_l(my_os, name, val):
    """
    Case: required version < installed version
    """
    version = val.get('version', None)

    # Usually we don't have this case.
    print "Package %s (%s) with higher version installed but require lower version (%s). Installing..." % \
          (name, installed_packages[name], version)
    install_package(my_os, name, val)


def test_package(my_os, name, val):
    """
    Check installation
    """
    version = val.get('version', None)

    if name in installed_packages:
        if not version:
            print "Package %s (%s) installed. Skipping..." % (name, installed_packages[name])
            return

        if LooseVersion(version) > LooseVersion(installed_packages[name]):
            test_package_g(my_os, name, val)
        elif LooseVersion(version) == LooseVersion(installed_packages[name]):
            test_package_e(my_os, name, val)
        else:
            test_package_l(my_os, name, val)
    else:
        print "Package %s not installed. Installing..." % name
        install_package(my_os, name, val)


def build_package_str(my_os, name, val):
    """
    Build package installation string
    """
    package_str = None

    if my_os in ['win']:
        if val.get('wheel', None):
            package_str = val['wheel']
        elif val.get('version', None):
            # Win doesn't support >= or <=. Replace with ==
            op = val['test']
            op = re.sub('[><]', '=', op) if not op else op
            package_str = "%s%s%s" % (name, op, val['version'])
        else:
            package_str = name
    elif my_os in ['mac', 'lin']:
        if val.get('test', None) and val.get('version', None):
            package_str = "%s%s%s" % (name, val['test'], val['version'])
        else:
            package_str = "%s" % name

    return package_str


def get_os():
    """
    Retrieve OS
    """
    sy = platform.system()

    my_os = None
    # OS: windows
    if sy == 'Windows':
        my_os = 'win'
    # OS: Linux
    elif sy == 'Linux':
        my_os = 'lin'
    # OS: Mac
    else:
        my_os = 'mac'

    return my_os


def get_requirements_by_os(my_os):
    """
    Update requirements based on OS
    """
    reqs = {name: val for (name, val) in requirements.iteritems() if my_os in val['platform']}

    # OS: Mac or Linux. No wheel needed
    if my_os in ['mac', 'lin']:
        for (name, val) in reqs.iteritems():
            if 'wheel' in val:
                val.pop('wheel')

    # OS: Linux. No version for some packages
    if my_os in ['lin']:
        for name in ['numpy', 'scipy']:
            if 'version' in reqs[name]:
                reqs[name].pop('version')
            if 'test' in reqs[name]:
                reqs[name].pop('test')

    # Keep packages in order
    reqs_ordered_dict = OrderedDict()

    for i in range(len(order_requirements)):
        name = order_requirements[i]
        if name in reqs:
            reqs_ordered_dict[name] = reqs.pop(name)

    for (name, val) in reqs.iteritems():
        reqs_ordered_dict[name] = val

    return reqs_ordered_dict


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
        print "Not able to automatically install packages via apt-get.  Please meke sure the following dependencies are installed on your system:"
        print pre_requisites
    except:
        print "Unexpected error checking for apt-get:", sys.exc_info()[0]
        raise

    if supports_apt_get:
        for req in pre_requisites:
            print "Checking/Installing %s" % req
            check_call(['apt-get', 'install', '-y', req], stdout=open(os.devnull, 'wb'), stderr=STDOUT)


def install_packages(my_os, reqs):
    """
    Install required packages
    """
    if my_os in ['lin']:
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
              version='0.4',
              description='Facilitating submission and analysis of simulations',
              url='https://github.com/InstituteforDiseaseModeling/dtk-tools',
              author='Edward Wenger, Benoit Raybaud, Jaline Gerardin, Milen Nikolov, Aaron Roney, Nick Karnik, Zhaowei Du',
              author_email='ewenger@intven.com, braybaud@intven.com, jgerardin@intven.com, mnikolov@intven.com, aroney@intven.com, nkarnik@intven.com, zdu@intven.com',
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
        print "\nA previous simtools.ini configuration file is present. Attempt to auto-merge"
        merge_cp = ConfigParser()
        merge_cp.read([default_ini, current_simtools])

        # Backup copy the current
        print "Backup copy your current simtools.ini to simtools.ini.bak"
        shutil.copy(current_simtools, current_simtools + ".bak")

        # Write the merged one
        merge_cp.write(open(current_simtools, 'w'))
        print "Merged simtools.ini written!\n"

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

    cp.write(open(example_simtools, 'w'))


def upgrade_pip(my_os):
    """
    Upgrade pip before install other packages
    """
    import subprocess

    if my_os in ['mac', 'lin']:
        subprocess.call("pip install -U pip", shell=True)
    elif my_os in ['win']:
        subprocess.call("python -m pip install --upgrade pip", shell=True)


def main():
    # Check OS
    my_os = get_os()
    print 'os: %s' % my_os

    # Upgrade pip before install other packages
    upgrade_pip(my_os)

    # Get OS-specific requirements
    reqs = get_requirements_by_os(my_os)

    # Install required packages
    install_packages(my_os, reqs)

    # Consider config file
    handle_init()

    # Success !
    print "\n======================================================="
    print "| Dtk-Tools and dependencies installed successfully.  |"
    print "======================================================="


if __name__ == "__main__":
    # check os first
    if ctypes.sizeof(ctypes.c_voidp) != 8:
        print """\nFATAL ERROR: dtk-tools only supports Python 2.7 x64. Please download and install a x86-64 version of python at:
        - Windows: https://www.python.org/downloads/windows/
        - Mac OSX: https://www.python.org/downloads/mac-osx/
        - Linux: https://www.python.org/downloads/source/\n
        Installation is now exiting..."""
        exit()

    main()
