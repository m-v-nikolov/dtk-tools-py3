from json2dict import json2dict as j2d
from np2pd import np2pd as n2p
from dict2pd import dict2pd as d2p
from pd2csv import pd2csv as p2c
from bin2np import bin2np as b2n  
from np2json import np2json as n2j
import numpy as np
import pprint as pp



''' json2dict examples'''

# filter all items matching a condition
test = j2d("tags.json", False, (lambda data: (data, False) if "B" in data else (None, False)))
pp.pprint(test, depth=3)

# stop parsing when an item is found
test = j2d("tags.json", False, (lambda data: (data, True) if "B" in data else (None, False)))
pp.pprint(test, depth=3)

# load an entire json file
test = j2d("config.json")
pp.pprint(test, depth=3)



''' np2pd examples'''

# convert to pandas series
test = n2p(np.array([1, 2, 3, 4 ,5 ]), to_series=True)
print "1D to series"
print test

# convert to pandas data frame
test = n2p(np.array([1, 2, 3, 4 ,5]), to_series=False)
print "1D to data frame"
print test  

# 2D examples
arr = np.array([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]])

# flatten to pandas series
test = n2p(arr, to_series=True)
print "2D to series"
print test

# 2D to data frame 
test = n2p(arr, to_series=False)
print "2D to data frame"
print test   



''' dict2pd examples'''

# single level dictionary
d = {'a':1, 'b':2, 'c':3}
test = d2p(d)

print "single level dict 2 data frame"
print test


d = {'a':1, 'b':2, 'c':{'ca':[3,4]}}
test = d2p(d)

print "multi level dict 2 data frame"
# notice that the dict is NOT decomposed in MultiLevel index
print test



''' pd2csv examples'''

d = {'a':1, 'b':2, 'c':3}
df = d2p(d)
p2c(df)
print "data frame to csv; default csv file location ./dataframe.csv"

p2c(df, "C:\Users\Mnikolov\Dropbox\my_data.csv")
print "data frame to csv; save to a file my_data.csv in Dropbox"


d = {'a':1, 'b':2, 'c':{'ca':[3,4]}}
test = d2p(d)
# notice that the dict is NOT decomposed in MultiLevel index
print "multilevel dict based data frame to csv: file is not saved to csv; (can't decompose multi-level dicts to MultiIndex data frames to tupled csv files at this time) "



''' bin2np examples'''

# read a binary file
test = b2n('scales.npy')
print test


# read only even numbers separated by ", " comma-space  from a text file
test = b2n('numbers.txt', func = lambda x: (True, True) if x%2 == 0 else (False, True), sep=', ')
print "even numbers"
print test

# stop parsing after reading the first even number
test = b2n('numbers.txt', func = lambda x: (True, False) if x%2 == 0 else (False, True), sep=", ")
print "first even number"
print test



''' np2json examples'''

arr = np.array([1, 2, 3, 4 ,5])
n2j(arr)

test = j2d("data.json")
print "load json generated from 1D numpy array"
print test

arr = np.array([[1, 2, 3, 4 ,5],[6, 7, 8, 9, 10]])
n2j(arr)

test = j2d("data.json")
print "load json generated from 2D numpy array"
print test

# arrays with dimensions greater than 2 are NOT supported at present




