import ctypes
import glob
import os
import platform
import shutil
import sys
from ConfigParser import ConfigParser
from distutils.version import LooseVersion
from simtools.utils import nostdout

if ctypes.sizeof(ctypes.c_voidp) != 8 :
    print """\nFATAL ERROR: dtk-tools only supports Python 2.7 x64. Please download and install a x86-64 version of python at:
    - Windows: https://www.python.org/downloads/windows/
    - Mac OSX: https://www.python.org/downloads/mac-osx/
    - Linux: https://www.python.org/downloads/source/\n
    Installation is now exiting..."""
    exit()

# Set the list of requirements here
# Can either take package==version or package
# For Windows, the wheel can be provided in either tar.gz or whl format\
requirements = [
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

current_directory = os.path.dirname(os.path.abspath(__file__))
install_directory = os.path.join(current_directory, 'install')

if platform.architecture() == ('64bit', 'WindowsPE'):
    # For windows + python x64 -> use the wheel
    import pip

    # Get the installed package to not reinstall everything
    installed_packages = dict()
    # Flatten the list
    for package in pip.get_installed_distributions():
        installed_packages[package.project_name] = package.version

    def install_package(package):
        pip.main(['install', package])

    def update_package(package,version=None):
        if '.whl' in package or '.tar.gz' in package:
            install = package
        else:
            install = "%s==%s"%(package,version) if version else package

        pip.main(['install', install, '--upgrade'])

    def test_package(name, version=None, package=None):
        if package is None:
            package = name

        if name in installed_packages:
            if version and LooseVersion(version) > LooseVersion(installed_packages[name]):
                print "Package: %s installed but with version %s. Upgrading to %s..." % (name, installed_packages[name], version)
                # The version we want is ahead -> needs update
                update_package(package, version)
            else:
                print "Package %s (%s) already installed and in correct version. Skipping..." % (name, installed_packages[name])
        else:
            print "Package: %s (%s) not installed. Installing..." % (name,version)
            # No version found -> install
            install_package(package)

    # Go through the requirements
    for requirement in requirements:
        # Split on == to get name and version (if any)
        package_name = requirement.split('==')[0]
        package_name = package_name.replace('-','_')

        version = requirement.split('==')[1] if '==' in requirement else None

        # Find the associated wheel
        glob_search = glob.glob(os.path.join(install_directory,'%s*' % package_name))
        wheel = glob_search[0] if len(glob_search) > 0 else None

        # Test the presence of the package
        test_package(package_name, version, wheel)

    # Remove the requirements for windows (because we handled them manually)
    requirements = []

if platform.architecture() == ('64bit', ''):
    # Removes curses for MacOSx (built-in)
    requirements.remove('curses==2.2')

if platform.system() == 'Linux':
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
        check_call('apt-get -h',stdout=open(os.devnull, 'wb'), stderr=STDOUT)
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
            check_call(['apt-get', 'install', '-y', req],stdout=open(os.devnull, 'wb'), stderr=STDOUT)

    # We are on linux, change some requirements
    if 'curses==2.2' in requirements: # Could have been removed by 64bit architecture above
        requirements.remove('curses==2.2')
    requirements.remove('numpy==1.11.1+mkl')
    requirements.remove('scipy==0.18.0')
    requirements.append('numpy')
    requirements.append('scipy')

# Add the develop by default
sys.argv.append('develop')
sys.argv.append('--quiet')

from setuptools import setup, find_packages
# Suppress the outputs except the errors
with nostdout(stderr=True):
    setup(name='dtk-tools',
          version='0.3.5',
          description='Facilitating submission and analysis of simulations',
          url='https://github.com/InstituteforDiseaseModeling/dtk-tools',
          author='Edward Wenger, Benoit Raybaud, Jaline Gerardin, Milen Nikolov, Aaron Roney, Nick Karnik, Zhaowei Du',
          author_email='ewenger@intven.com, braybaud@intven.com, jgerardin@intven.com, mnikolov@intven.com, aroney@intven.com, nkarnik@intven.com, zdu@intven.com',
          packages=find_packages(),
          install_requires=requirements,
          entry_points={
              'console_scripts': ['calibtool = calibtool.commands:main', 'dtk = dtk.commands:main']
          },
          package_data={'': ['simtools/simtools.ini']},
          zip_safe=False)

# Copy the default.ini into the right directory if not already present
current_simtools = os.path.join(current_directory,'simtools','simtools.ini')
default_ini = os.path.join(install_directory,'default.ini')
if not os.path.exists(current_simtools):
    shutil.copyfile(default_ini, current_simtools)
else:
    # A simtools was already present, merge the best we can
    print "\nA previous simtools.ini configuration file is present. Attempt to auto-merge"
    merge_cp = ConfigParser()
    merge_cp.read([default_ini, current_simtools])

    # Backup copy the current
    print "Backup copy your current simtools.ini to simtools.ini.bak"
    shutil.copy(current_simtools, current_simtools+".bak")

    # Write the merged one
    merge_cp.write(open(current_simtools,'w'))
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
    cp.set('EXAMPLE','type','LOCAL')
    cp.set('EXAMPLE','input_root', os.path.join(current_directory,'examples','inputs'))

cp.write(open(example_simtools,'w'))

# Success !
print "\n======================================================="
print "| Dtk-Tools and dependencies installed successfully.  |"
print "======================================================="
