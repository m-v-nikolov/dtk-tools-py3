try:
    from COMPSJavaInterop import COMPSJavaInterop
except ImportError:
    print('Failed loading COMPSJavaInterop package; you will only be able to run local simulations.')
except KeyError:
    print('Unable to determine JAVA_HOME; please set JAVA_HOME environment variable as described in pyCOMPS README.txt')

__all__ = []
