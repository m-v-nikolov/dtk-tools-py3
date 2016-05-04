import os
from setuptools import setup, find_packages
import platform


if platform.architecture() == ('64bit', 'WindowsPE'):
    # For windows + python x64 -> use the wheel
    import pip

    def install_package(package):
        pip.main(['install',package])

    current = os.path.dirname(os.path.abspath(__file__))
    install = os.path.join(current,'install')
    install_package(os.path.join(install,'scipy-0.17.0-cp27-none-win_amd64.whl'))
    install_package(os.path.join(install,'numpy-1.11.0+mkl-cp27-cp27m-win_amd64.whl'))
    install_package(os.path.join(install,'matplotlib-1.5.1-cp27-none-win_amd64.whl'))
    install_package(os.path.join(install,'pandas-0.18.0-cp27-cp27m-win_amd64.whl'))
    install_package(os.path.join(install,'seaborn-0.7.0-py2.py3-none-any.whl'))
    install_package(os.path.join(install,'statsmodels-0.6.1-cp27-none-win_amd64.whl'))
    install_package(os.path.join(install,'npyscreen-4.10.5.tar.gz'))
    install_package(os.path.join('psutil'))


setup(name='simtools',
      version='0.1',
      description='Facilitating submission and analysis of simulations',
      url='https://github.com/InstituteforDiseaseModeling/dtk-tools',
      author='Edward Wenger, Benoit Raybaud, Jaline Gerardin, Milen Nikolov',
      author_email='ewenger@intven.com, braybaud@intven.com, jgerardin@intven.com, mnikolov@intven.com',
      packages=find_packages(),
      install_requires=[
          'matplotlib',
          'pandas',
          'psutil',
          'seaborn',
          'statsmodels',
          'npyscreen'
      ],
      package_data={'': ['simtools.cfg']},
      zip_safe=False)


setup(name='dtk',
      version='0.3',
      description='Facilitating DTK disease model configuration, submission, and analysis',
      url='https://github.com/InstituteforDiseaseModeling/dtk-tools',
      author='Edward Wenger, Benoit Raybaud, Jaline Gerardin, Milen Nikolov',
      author_email='ewenger@intven.com, braybaud@intven.com, jgerardin@intven.com, mnikolov@intven.com',
      packages=['dtk'],
      install_requires=[
          'simtools'
      ],
      entry_points={
          'console_scripts': ['dtk = dtk.commands:main']
      },
      package_data={'': ['dtk_setup.cfg']},
      zip_safe=False)

setup(name='calibtool',
      version='0.1',
      description='Calibration of simulation model parameterizations',
      url='https://github.com/InstituteforDiseaseModeling/dtk-tools',
      author='Edward Wenger, Benoit Raybaud, Jaline Gerardin, Milen Nikolov',
      author_email='ewenger@intven.com, braybaud@intven.com, jgerardin@intven.com, mnikolov@intven.com',
      packages=['simtools'],
      install_requires=[
          'scipy',
          'simtools'
      ],
      entry_points={
          'console_scripts': ['calibtool = calibtool.commands:main']
      },
      zip_safe=False)
