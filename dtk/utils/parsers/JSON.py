import re
import json
from json import JSONDecoder
from functools import partial

# consider configuring a data-path variable listing directories of interest
# that may store json and other data files (?)

# would per scenario directory structure schema be feasible (?) 
# e.g.

# scnenario_name\
#         \data
#         \scripts
#         \workflow
#         \simulations
#         \figures
#         .dtk_proj        # project json/xml schema (similar to vs sln file)


# remove all white space that is outside quotes
def strip(pieces):
    sub_pieces = pieces.split('"')
    for i, sub_piece in enumerate(sub_pieces):
        if not i % 2:
            sub_pieces[i] = re.sub("\s+", "", sub_piece)
    return '"'.join(sub_pieces)


# parse the json file object by object, 1024 bytes at a time
# every 1024 bytes check if pieces contain a valid json object
# if not, accumulate more pieces 1024 bytes at a time 
#
# save memory in the process and allow 
# various types of objects to be parsed
# that way we can get a dictionary of mixed types
# (e.g. lists, other dictionaries, etc.
#
# by default REMOVE all new lines
def parse(input_data, decoder = JSONDecoder(), pieces_mem = 1024):    
    pieces = ''
    for piece in iter(partial(input_data.read, pieces_mem), ''):
        pieces = pieces + piece
        #pieces =  pieces.replace('\n','')
        pieces = strip(pieces)
        #print pieces
        while pieces:
            try:
                j, idx = decoder.raw_decode(pieces)
                yield j
                pieces = pieces[idx:]
            except ValueError:
                break

# reads json file to a dictionary

# if as_is is True read whatever object is stored in the json file and return it;
# otherwise, if as_is is False, read the json file object by object and return 
# a dictionary of objects
#
#   dict = {
#            1 : obj_1,
#            2: obj_2,
#            ...
#            }
#
# if as_is is False and func is not None, apply func to data 
# return a tuple containing the object to be stored in the dictionary and boolean value;
# if boolean is True keep parsing the json file, else break and stop parsing the json file
# (may be useful for filtering or searching until a certain item is found after which we do
# not process the rest of the json file or continue processing it)
# if func returns None stop parsing the json file and return the dictionary; else create a new dictionary entry with the returned object
#
# Example: with input file "cluster_tags_alt.json" containing 
'''
{"B":{"a":1}}


{"a":{"tags  a":{"alt":2}}}

{
    "idx0":4,
    "idx1":0.324
}

{"B":{"b":1}}

[1, 2, 3, 4]  

  {"4 ":   435435,"asd":"asdasd"}
'''
'''

test = json2dict("cluster_tags_alt.json", False, (lambda data: (data, False) if "B" in data else (None, False)))

Output:

{0: {u'B': {u'a': 1}}, 3: {u'B': {u'b': 1}}}

'''

def json2dict(json_file, as_is = True, func = None):
    
    with open(json_file, 'Ur') as input_data:
        if as_is:
            data = json.load(input_data)
            return data
        else:
            data_dict = {}
            for i,data in enumerate(parse(input_data)):
                if not func is None:
                    data, do_break = func(data)
                    if not data is None:
                        data_dict[i] = data
                    if do_break:
                        break
                else:
                    data_dict[i] = data
            return data_dict

def dict2json(filename,dict_content):
    with open(filename,'w') as f:
        f.write(content)