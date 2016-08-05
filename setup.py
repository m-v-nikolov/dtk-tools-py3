import glob
import os
import shutil

import re
from setuptools import setup, find_packages
import platform

# Set the list of requirements here
# Can either take package==version or package
# For Windows, the wheel can be provided in either tar.gz or whl format
requirements = [
    'matplotlib==1.5.1',
    'pandas==0.18.1',
    'seaborn==0.7.0',
    'statsmodels==0.6.1',
    'npyscreen==4.10.5',
    'curses==2.2',
    'scipy==0.17.0',
    'validators'
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

    def update_package(package):
        pip.main(['install', package, '--upgrade'])

    def mycmp(version1, version2):
        def normalize(v):
            return [int(x) for x in re.sub(r'(\.0+)*$', '', v).split(".")]

        return cmp(normalize(version1), normalize(version2))

    def test_package(name, version=None, package=None):
        if name in installed_packages:
            if version and mycmp(version, installed_packages[name]) > 0:
                print "Package: %s installed but with version %s. Upgrading to %s..." % (name, installed_packages[name], version)
                # The version we want is ahead -> needs update
                update_package(package)
            else:
                print "Package %s (%s) already installed and in correct version. Skipping..." % (name, installed_packages[name])
        else:
            print "Package: %s (%s) not installed. Installing..." % (name,version)
            # No version found -> install
            if package is None:
                package = name
            install_package(package)

    # Go through the requirements
    for requirement in requirements:
        # Split on == to get name and version (if any)
        package_name = requirement.split('==')[0]
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
if not os.path.exists(os.path.join(current_directory,'simtools','simtools.ini')):
    shutil.copyfile(os.path.join(install_directory,'default.ini'), os.path.join(current_directory,'simtools','simtools.ini'))