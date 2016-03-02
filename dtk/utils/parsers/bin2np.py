import numpy as np


# parse a binary numeric file
#
# if dtype is not None, try constructing an array from 
# text/binary file containing numbers of type dtype (e.g. floats)
# by default read the whole file;
# 
# if dtype and sep are not None read a text file containing numbers separated 
# by sep
# note that providing dtype leads to more efficient file load 
#
# if dtype is None just load the data from a pickled/.npy/.npz file
# see http://docs.scipy.org/doc/numpy/reference/generated/numpy.load.html
# 
# if func is not None
# func must be a truth assignment function mapping each LINE in a TEXT file to a tuple (boolean, boolean)
# each number in the file is separated by sep; if sep is None the default delimiter is white space
# all parsed numbers are treated as floats at present
# if func returns 
#    (True, True): the value in the file is read and the parsing continues
#    (True, False): the value in the file is read and the parsing stops
#    (False, True): the value in the file is skipped and the parsing continues
#    (False, False): the value in the file is skipped and the parsing stops


def filter_generator(src, func, sep=" "):
    for line in src:
        xs = line.split(sep)
        for x in xs:
            read, goon = func(float(x))
            if not read and not goon:
                return
            if read and not goon:
                yield x
                return
            if read and goon:
                yield x
            if not read and goon:
                pass
  
def bin2np(src, func = None, sep = " "):
    if not func is None:
        with open(src) as f:
            return np.genfromtxt(filter_generator(f, func, sep))
    else:
        return np.load(src)