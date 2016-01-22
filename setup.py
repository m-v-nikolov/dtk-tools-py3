from setuptools import setup, find_packages

setup(name='dtk',
      version='0.3',
      description='Facilitating DTK disease model configuration, submission, and analysis',
      url='https://github.com/InstituteforDiseaseModeling/dtk-tools',
      author='Edward Wenger',
      author_email='ewenger@intven.com',
      packages=find_packages(),
      install_requires=[
          'psutil>=3.1.1',
          'matplotlib',
          'pandas'
      ],
      entry_points = {
        'console_scripts': ['dtk = dtk.commands:main']
      },
      package_data = { '': ['dtk_setup.cfg'] },
      zip_safe=False)
