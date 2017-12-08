# Create a builder
from simtools.COMPSAccess.Builder import Builder

builder = Builder(name='test', dynamic_parameters={'Run_Number':[1,2,3]})
print(builder.wo)
