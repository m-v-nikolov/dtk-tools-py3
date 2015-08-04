try:
    from COMPSJavaInterop import COMPSJavaInterop
except ImportError:
    print("Failed loading COMPSJavaInterop package; you will only be able to run local simulations")

__all__ = [ "interventions", "malaria", "vector", "utils", "generic", "tools" ]
