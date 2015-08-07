Modifying updater for new parameter sampling method
----------------------------------------------------

The script containing instructions for selecting the next round of
parameters is next_parameters.py. Any new updater should be called
from update_params() in this script using a keyword specified here and
in the calibration manager.

next_parameters.py includes a box_prior_generator() that generates a
prior function from the list of parameters and ranges specified by the
user.

