from setuptools import setup

setup(name='dtk',
      version='0.1',
      description='Facilitating DTK disease model configuration, submission, and analysis',
      url='https://github.com/edwenger/dtk',
      author='Edward Wenger',
      author_email='ewenger@intven.com',
      packages=['dtk'],
      install_requires=[
          'psutil',
          'matplotlib',
          'pandas'
      ],
      entry_points = {
        'console_scripts': ['dtk = dtk.commands:main']
      },
      zip_safe=False)
