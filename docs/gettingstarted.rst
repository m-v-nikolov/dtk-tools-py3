Getting started
===============

Installation
------------

.. contents::
    :local:


Pre-requisites
``````````````

In order to use the tools, you will need a x64 version of Python 3.6. To verify which Python is installed on your computer, issue a: `python` and the output should look like::

    Python 3.6.1 (v3.6.1:69c0db5, Mar 21 2017, 18:41:36) [MSC v.1900 64 bit (AMD64)] on win32

Then you will need to clone the dtk-tools repository. ::

    git clone https://github.com/InstituteforDiseaseModeling/dtk-tools.git

Windows installation
````````````````````

On Windows, navigate to the dtk-tools directory and issue a ::

    python setup.py

All the Python dependencies along with the package will be installed on your machine.

To finish, in order to use dtk-tools from everywhere on your system, ddd the path to the dtk_tools folder to your `PYTHONPATH` environment variable.

CentOS 7 installation
`````````````````````
Note: This install guide assumes you are running CentOS 7.
Also it assumes you have a desktop environment (pyCOMPS require a display in order to allow COMPS login box to appear).

Installation of Python 3.6
~~~~~~~~~~~~~~~~~~~~~~~~~~

Update the system and download some pre-requisites::

    yum update -y
    yum install yum-utils -y
    yum groupinstall development -y
    yum install snappy-devel -y
    yum install openssl-devel -y

Install Python::

    yum install https://centos7.iuscommunity.org/ius-release.rpm
    yum install python36u

Make sure Python is installed by issuing a::

    python3.6 -V

Install pip and other dev packages::

    yum install python36u-pip
    yum install python36u-devel
    yum install python36u-tkinter

Create a virtual environment::

    python3.6 -m venv idm

Activate the idm environment::

    source idm/bin/activate

Installation of dtk-tools
~~~~~~~~~~~~~~~~~~~~~~~~~

Clone the repository::

    git clone https://github.com/InstituteforDiseaseModeling/dtk-tools.git

Install the tools::

    cd dtk-tools
    python setup.py

Download and install pyCOMPS::

    curl -O https://institutefordiseasemodeling.github.io/PythonDependencies/pyCOMPS-2.1-py2.py3-none-any.whl
    pip install pyCOMPS-2.1-py2.py3-none-any.whl

MAC OSX installation
````````````````````
Tested with macOS Sierra (Version 10.12)

Make sure you have the Xcode Command Line Tools installed::

    xcode-select --install

By default, MAC will install Python 2.7.10 for system use and users may not have certain permissions to upgrade some packages. We will leave the system Python unchanged and install our own Python instead::

    /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

Refer to http://brew.sh/index.html

Install Python with the command::

    brew install python3

Install virtualenv::

    pip3 install virtualenv

Then navigate inside the `dtk-tools` directory and create an IDM virtual environment::

    virtualenv idm

Activate the virtual environment (you will have to do activate the virtual environment first before using dtk-tools)::

    source ./idm/bin/activate

Make sure you are in the virtual environment by checking if the prompt displays `(idm)` at the beginning as shown::

    (idm) my-computer:dtk-tools

Download and install pyCOMPS::

    curl -O https://institutefordiseasemodeling.github.io/PythonDependencies/pyCOMPS-2.1-py2.py3-none-any.whl
    pip3 install pyCOMPS-2.1-py2.py3-none-any.whl

Navigate inside the `dtk-tools` folder and install dtk-tools::

    python setup.py

.. note::
    If you are encountering issues with TK on OSX (for example not being able to plot, or some matplotlib related issues), try:

    .. code-block:: bash

        brew install homebrew/dupes/tcl-tk
        brew uninstall python3
        brew install python3 --with-brewed-tk

Testing your installation
-------------------------
To ensure your installation is working properly, you can issue a::

    dtk version

Which should display::

    ____    ______  __  __          ______                ___
    /\  _`\ /\__  _\/\ \/\ \        /\__  _\              /\_ \
    \ \ \/\ \/_/\ \/\ \ \/'/'       \/_/\ \/   ___     ___\//\ \     ____
     \ \ \ \ \ \ \ \ \ \ , <    _______\ \ \  / __`\  / __`\\ \ \   /',__\
      \ \ \_\ \ \ \ \ \ \ \\`\ /\______\\ \ \/\ \L\ \/\ \L\ \\_\ \_/\__, `\
       \ \____/  \ \_\ \ \_\ \_\/______/ \ \_\ \____/\ \____//\____\/\____/
        \/___/    \/_/  \/_/\/_/          \/_/\/___/  \/___/ \/____/\/___/
    Version: 1.0b3

You can also follow the recipe about :doc:`cookbook/firstsimulation`.

Configuration of the tools
--------------------------

To configure your user-specific paths and settings for local and HPC job submission, edit the properties in ``simtools/simtools.ini``.
To learn more about the available options, please refer to :doc:`simtools/simtoolsini`.

One can verify the proper system setup by navigating to the ``test`` directory and running the unit tests contained therein, e.g. by executing ``nosetests`` if one has the `nose <http://nose.readthedocs.org/en/latest/index.html>`_ package installed.
