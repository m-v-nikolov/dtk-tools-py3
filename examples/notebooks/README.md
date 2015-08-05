# IPython examples

## Installation of Python

Python 2.7 is required to run all the examples. This guide assumes that Python is installed in C:\Python27.
If you do not have python installed, you can find the installer here: (https://www.python.org/downloads/)

## Installation of Microsoft Visual C++ Compiler

In order to install certain python libraries necessary to run the scripts and examples, you need to have a correct version of the Microsoft Visual C++ Compiler. Fortunately, you can install the following package (http://www.microsoft.com/en-us/download/details.aspx?id=44266) that will enable pip to build libraries. 

## Installation of the dependencies

First of all, make sure to update to the latest version of pip by using:
```
pip install --upgrade pip
```
In a command prompt, use pip to install the required packages:
```
pip install matplotlib
pip install psutil
pip install pandas
pip install "ipython[all]"
```

### Installation of the DTK package

The DTK package is installed through pip directly from the GitHub repository:
```
pip install git+https://github.com/edwenger/dtk#egg=dtk
```

### EMOD Model

This tutorial assumes that you have a working version of the EMOD 2.0 model (http://idmod.org/software).
You can find the Eradication.exe file in %userprofile%\appdata\local\EMOD\QuickStart\v2.0.0

## Getting started

The tutorials are supposed to be done sequentially.
To get started, open a command prompt and navigate to the folder containing this Readme file. 
Then start the notebook server by typing:
```
ipython notebook
```
A browser should open to http://localhost:8888/tree. You can navigate to the Examples folder and open the 01 - Welcome workbook by clicking on it.
