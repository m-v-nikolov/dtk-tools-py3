from setuptools import setup, find_packages

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
          'psutil>=3.1.1'
      ],
      package_data = { '': ['simtools.cfg'] },
      zip_safe=False)

setup(name='dtk',
      version='0.3',
      description='Facilitating DTK disease model configuration, submission, and analysis',
      url='https://github.com/InstituteforDiseaseModeling/dtk-tools',
      author='Edward Wenger, Benoit Raybaud, Jaline Gerardin, Milen Nikolov',
      author_email='ewenger@intven.com, braybaud@intven.com, jgerardin@intven.com, mnikolov@intven.com',
      packages=find_packages(),
      install_requires=[
          'simtools'
      ],
      entry_points = {
        'console_scripts': ['dtk = dtk.commands:main']
      },
      package_data = { '': ['dtk_setup.cfg'] },
      zip_safe=False)

setup(name='calibtool',
      version='0.1',
      description='Calibration of simulation model parameterizations',
      url='https://github.com/InstituteforDiseaseModeling/dtk-tools',
      author='Edward Wenger, Benoit Raybaud, Jaline Gerardin, Milen Nikolov',
      author_email='ewenger@intven.com, braybaud@intven.com, jgerardin@intven.com, mnikolov@intven.com',
      packages=find_packages(),
      install_requires=[
          'scipy',
          'simtools'
      ],
      entry_points = {
        'console_scripts': ['calibtool = calibtool.commands:main']
      },
      zip_safe=False)
