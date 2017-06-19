================
Disease packages
================

Commands for querying and installing disease packages (same as the last disease/dtk-tools decoupling):
Three commands are available for querying and downloading disease-specific packages:
•	dtk list_packages
•	dtk list_package_versions
•	dtk get_package

Disease packages will be globally installed via ‘pip install’.
Installing another version of a previously installed disease package will overwrite the original. Only one version per disease may be used.
The latest (highest numerically, highest significant digits to the left) version is obtained if -v (or --version) PACKAGE_VERSION is not specified.
How to use an installed package:

All python modules and files within disease packages are imported recursively so that a simple “import NAME” command is sufficient to access everything in the full package.

How to create and manage a dtk-tools disease repository

The dtk-tools commands to query and retrieve disease packages depends on the structure of the relevant GitHub repository

Pick a new package NAME, e.g. ‘malaria’

Pick a new GitHub REPOSITORY name. It is arbitrary, though it is best to pick something meaningful (e.g. ‘malaria-package’)

Create the REPOSITORY in the IDM GitHub account: https://github.com/InstituteforDiseaseModeling

Create a setup.py file in the root of the new repository that has exactly the following in it (substitute ‘malaria’ with the NAME of the new disease package, not REPOSITORY name):
from setuptools import setup, find_packages

setup(name='malaria',
version='$VERSION$',
packages=find_packages(),
install_requires=[]
)
5.	Create a directory in the new repository with the same NAME as your new package. All of your package modules/files go in here. The root of your new repository should look something like this:

Register the REPOSITORY name in the package-repository file located at: DTK_TOOLS_ROOT/simtools/Utilities/GitHub/repository_map.json (e.g. malaria package mapping shown):
‘NAME’: ‘REPOSITORY’ format

For the new package to be usable by dtk-tools, it needs to have at least one version specified. Versions are specified with tags of a particular format: release-VERSIONNUMBER . Any other tags are ignored and may be used for internal purposes.

New versions (properly formatted tags) are instantly available to all compatible versions of dtk-tools.

Versions must be of the form: n1.n2.n3 … where nX are non-negative integers that do not contain leading zeros. Any number of digits (1+) may be specified, though each individual package must use the same number of digits for all versions (e.g. perhaps malaria always uses 3 digits, HIV 2 digits, etc). Valid examples: release-1.0.0 , release-1.2.3.4.5.6.7 , release-7

Done!