Getting started
===============

Installation
------------

.. contents::
    :local:


Pre-requisites
``````````````

In order to use the tools, you will need a x64 version of Python 2.7. To verify which Python is installed on your computer, issue a: `python` and the output should look like::

    Python 2.7.13 (v2.7.13:a06454b1afa1, Dec 17 2016, 20:53:40) [MSC v.1500 64 bit (AMD64)] on win32

Then you will need to clone the dtk-tools repository. ::

    git clone https://github.com/InstituteforDiseaseModeling/dtk-tools.git

Windows installation
````````````````````

On Windows, navigate to the dtk-tools directory and issue a ::

    python setup.py

All the Python dependencies along with the package will be installed on your machine.

To finish, in order to use dtk-tools from everywhere on your system, ddd the path to the dtk_tools folder to your `PYTHONPATH` environment variable.

MAC OSX installation
````````````````````
Tested with macOS Sierra (Version 10.12)

Make sure you have the Xcode Command Line Tools installed::

    xcode-select --install

By default, MAC will install Python 2.7.10 for system use and users may not have certain permissions to upgrade some packages. We will leave the system Python unchanged and install our own Python instead::

    /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

Refer to http://brew.sh/index.html

Install Python with the command::

    brew install python

Install virtualenv::

    pip install virtualenv

Then navigate inside the `dtk-tools` directory and create an IDM virtual environment::

    virtualenv idm

Activate the virtual environment (you will have to do activate the virtual environment first before using dtk-tools)::

    source ./idm/bin/activate

Make sure you are in the virtual environment by checking if the prompt displays `(idm)` at the beginning as shown::

    (idm) my-computer:dtk-tools

Install pyCOMPS (wheel available `here <https://institutefordiseasemodeling.github.io/PythonDependencies/pyCOMPS-1.0.1-py2.py3-none-any.whl>`_ )::

    pip install pyCOMPS-1.0.1-py2.py3-none-any.whl

Navigate inside the `dtk-tools` folder and install dtk-tools::

    python setup.py

.. note::
    If you are encountering issues with TK on OSX (for example not being able to plot, or some matplotlib related issues), try:

    .. code-block:: bash

        brew install homebrew/dupes/tcl-tk
        brew uninstall python
        brew install python --with-brewed-tk


Configuration of the tools
--------------------------

To configure your user-specific paths and settings for local and HPC job submission, edit the properties in ``simtools/simtools.ini``.
To learn more about the available options, please refer to :doc:`simtools/simtoolsini`.

One can verify the proper system setup by navigating to the ``test`` directory and running the unit tests contained therein, e.g. by executing ``nosetests`` if one has the `nose <http://nose.readthedocs.org/en/latest/index.html>`_ package installed.
