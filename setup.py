import ctypes
import glob
import os
import platform
import shutil
import sys
from ConfigParser import ConfigParser
from distutils.version import LooseVersion
from simtools.utils import nostdout

current_directory = os.path.dirname(os.path.abspath(__file__))
install_directory = os.path.join(current_directory, 'install')

installed_packages = dict()

# Set the list of requirements here
# Can either take package==version or package
# For Windows, the wheel can be provided in either tar.gz or whl format\
requirements = {
    'curses': {
        'platform': ['win'],
        'version': '2.2',
        'test': '==',
        'wheel': 'http://www.lfd.uci.edu/%7Egohlke/pythonlibs/dp2ng7en/curses-2.2-cp27-none-win_amd64.whl'
    },
    'matplotlib': {
        'platform': ['win', 'lin', 'mac'],
        'version': '1.5.3',
        'test': '>=',
        'wheel': 'http://www.lfd.uci.edu/~gohlke/pythonlibs/dp2ng7en/matplotlib-1.5.3-cp27-cp27m-win_amd64.whl'
    },
    'numpy': {
        'platform': ['win', 'lin', 'mac'],
        'version': '1.11.1',
        'test': '==',
        'wheel': 'http://www.lfd.uci.edu/%7Egohlke/pythonlibs/dp2ng7en/numpy-1.11.1+mkl-cp27-cp27m-win_amd64.whl'
    },
    'pandas': {
        'platform': ['win', 'lin', 'mac'],
        'version': '0.18.1',
        'test': '==',
        'wheel': 'http://www.lfd.uci.edu/%7Egohlke/pythonlibs/dp2ng7en/pandas-0.18.1-cp27-cp27m-win_amd64.whl'
    },
    'psutil': {
        'platform': ['win', 'lin', 'mac'],
        'version': '4.3.0',
        'test': '==',
        'wheel': 'http://www.lfd.uci.edu/%7Egohlke/pythonlibs/dp2ng7en/psutil-4.3.1-cp27-cp27m-win_amd64.whl'
    },
    'python-snappy': {
        'platform': ['win', 'lin'],
        'version': '0.5',
        'test': '==',
        'wheel': 'http://www.lfd.uci.edu/%7Egohlke/pythonlibs/dp2ng7en/python_snappy-0.5-cp27-none-win_amd64.whl'
    },
    'scipy': {
        'platform': ['win', 'lin', 'mac'],
        'version': '0.18.0',
        'test': '==',
        'wheel': 'http://www.lfd.uci.edu/%7Egohlke/pythonlibs/dp2ng7en/scipy-0.18.0-cp27-cp27m-win_amd64.whl'
    },
    'seaborn': {
        'platform': ['win', 'lin', 'mac'],
        'version': '0.7.0',
        'test': '==',
        'wheel': 'http://www.lfd.uci.edu/%7Egohlke/pythonlibs/dp2ng7en/seaborn-0.7.1-py2.py3-none-any.whl'
    },
    'statsmodels': {
        'platform': ['win', 'lin', 'mac'],
        'version': '0.6.1',
        'test': '==',
        'wheel': 'http://www.lfd.uci.edu/%7Egohlke/pythonlibs/dp2ng7en/statsmodels-0.6.1-cp27-none-win_amd64.whl'
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
    },
    'test1': {
        'platform': ['win', 'lin', 'mac'],
        'version': '4.10.5',
        'test': '>='
    },
    'test2': {
        'platform': ['win', 'lin', 'mac'],
        'version': '0.10.6',
        'test': '=='
    },
    'test3': {
        'platform': ['win', 'lin', 'mac'],
    },
    'test4': {
        'platform': ['win', 'lin', 'mac'],
        'wheel': 'test4_some_install_url.whl'
    }
}


requirements_bk = [
    'numpy==1.11.1+mkl',
    'scipy==0.18.0',
    'matplotlib==1.5.1',
    'pandas==0.18.1',
    'seaborn==0.7.0',
    'statsmodels==0.6.1',
    'npyscreen==4.10.5',
    'curses==2.2',
    'validators',
    'SQLAlchemy==1.1.0b3',
    'python-snappy==0.5',
    'psutil==4.3.0',
    'networkx',
    'dill'
]


def get_installed_packages():
    """
    Check packages in system
    """
    import pip

    # Flatten the list
    for package in pip.get_installed_distributions():
        installed_packages[package.project_name] = package.version


def install_package(package_str):
    """
    Install package
    """
    import pip
    pip.main(['install', package_str])


def update_package(package_str):
    """
    Upgrade package
    """
    import pip
    pip.main(['install', package_str, '--upgrade'])


def test_package(name, val):
    """
    Check installation
    """
    package_str = build_package_str(name, val)

    if name in installed_packages:
        if hasattr(val, 'version'):
            version = val.get('version', None)
            if version and LooseVersion(version) > LooseVersion(installed_packages[name]):
                print "Package: %s installed but with version %s. Upgrading to %s..." % (
                name, installed_packages[name], version)
                # The version we want is ahead -> needs update
                # update_package(package_str)
            else:
                print "Package %s (%s) already installed and in correct version. Skipping..." % (name, installed_packages[name])
        else:
            print "Package %s (%s) already installed. Skipping..." % (name, installed_packages[name])
    else:
        print "Package: %s not installed. Installing..." % package_str
        # No version found -> install
        # install_package(package_str)

    # print 'package_str: %s' % package_str


def build_package_str(name, val, wheel=True):
    """
    Build package installation string
    """
    package_str = None

    if wheel and 'wheel' in val and val.get('wheel', None):
        package_str = val['wheel']
    elif 'version' in val and val.get('version', None):
        package_str = "%s%s%s" % (name, val['test'], val['version'])
    else:
        package_str = name

    return package_str


def get_os():
    """
    Retrieve OS
    """
    my_os = None
    # OS: windows
    if platform.architecture() == ('64bit', 'WindowsPE'):
        my_os = 'win'

    # OS: Mac
    if platform.architecture() == ('64bit', ''):
        my_os = 'mac'

    # OS: Linux
    if platform.system() == 'Linux':
        my_os = 'lin'

    return my_os


def get_requirements_by_os(my_os):
    """
    Update requirements based on OS
    """
    reqs = {req: val for (req, val) in requirements.iteritems() if my_os in val['platform']}

    # OS: Mac and Lin. No need wheel
    if my_os in ['mac', 'lin']:
        reqs = {req: val.pop('wheel' if 'wheel' in val else val) for (req, val) in reqs.iteritems()}

    # OS: Linux. No wheel or version for some packages
    if my_os == 'lin':

        reqs['numpy'].pop('version')
        reqs['numpy'].pop('test')

        reqs['scipy'].pop('version')
        reqs['scipy'].pop('test')

    return reqs


def install_packages(my_os, reqs):
    """
    Install required packages
    """

    # print 'In install_packages'
    # print 'Type of reqs: %s' % type(reqs)

    # OS: windows
    if my_os in ['win', 'mac']:
        # Get the installed package to not reinstall everything
        get_installed_packages()
        # import json
        # print json.dumps(reqs, indent=2)

        # Go through the requirements
        for (name, val) in reqs.iteritems():
            # Test the presence of the package
            # print req, val
            test_package(name, val)

        # Remove the requirements for windows (because we handled them manually)
        reqs = {}

    # OS: Linux
    if my_os in ['lin']:
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

    # Add the develop by default
    sys.argv.append('develop')
    sys.argv.append('--quiet')

    # requirements need to be a list for setup
    requirement_list = [build_package_str(name, val, False) for (name, val) in reqs.iteritems()]

    print requirement_list
    exit()

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
              install_requires=requirement_list,
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


def main():
    # Check OS
    my_os = get_os()

    # Testing
    my_os = 'lin'

    # Get OS-specific requirements
    reqs = get_requirements_by_os(my_os)

    import json
    print platform.architecture()
    print json.dumps(reqs, indent=2)

    # Install required packges
    install_packages(my_os, reqs)

    exit()

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