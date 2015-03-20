from setuptools import setup

setup(name='dtk',
      version='0.1',
      description='Facilitating DTK disease model configuration, submission, and analysis',
      url='https://github.com/edwenger/dtk',
      author='Edward Wenger',
      author_email='ewenger@intven.com',
      packages=['dtk'],
      install_requires=[
          'numpy',
          'matplotlib',
          'pandas'
      ],
      scripts=['dtk'],
      zip_safe=False)
