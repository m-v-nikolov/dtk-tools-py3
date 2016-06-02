import os

from SetupParser import SetupParser

try:
    os.environ['COMPS_REST_HOST'] = SetupParser().get('HPC', 'server_endpoint')
    from pyCOMPS import pyCOMPS

except ImportError:
    print('Failed loading pyCOMPS package; you will only be able to run local simulations.')

except KeyError:
    print('Unable to determine JAVA_HOME; please set JAVA_HOME environment variable as described in pyCOMPS README.txt')

__all__ = []
