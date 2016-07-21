import os
import shutil

from setuptools import setup, find_packages
import platform

requirements = [
    'matplotlib',
    'pandas',
    'seaborn',
    'statsmodels',
    'npyscreen',
    'curses',
    'scipy',
    'validators'
]

current_directory = os.path.dirname(os.path.abspath(__file__))
install_directory = os.path.join(current_directory, 'install')

if platform.architecture() == ('64bit', 'WindowsPE'):
    # For windows + python x64 -> use the wheel
    import pip

    def install_package(package):
        pip.main(['install', package])

    install_package(os.path.join(install_directory, 'scipy-0.17.0-cp27-none-win_amd64.whl'))
    install_package(os.path.join(install_directory, 'numpy-1.11.0+mkl-cp27-cp27m-win_amd64.whl'))
    install_package(os.path.join(install_directory, 'matplotlib-1.5.1-cp27-none-win_amd64.whl'))
    install_package(os.path.join(install_directory, 'pandas-0.18.0-cp27-cp27m-win_amd64.whl'))
    install_package(os.path.join(install_directory, 'seaborn-0.7.0-py2.py3-none-any.whl'))
    install_package(os.path.join(install_directory, 'statsmodels-0.6.1-cp27-none-win_amd64.whl'))
    install_package(os.path.join(install_directory, 'npyscreen-4.10.5.tar.gz'))
    install_package(os.path.join(install_directory, 'curses-2.2-cp27-none-win_amd64.whl'))
    install_package('validators')

if platform.architecture() == ('64bit', ''):
    # Removes curses for MacOSx (built-in)
    requirements.remove('curses')


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