from site_setup_functions import *

setup_functions = [config_setup_fn()]
reference_data = {}
analyzers = {}

def get_setup_functions() :

    return setup_functions

def load_reference_data(datatype) :

    return reference_data[datatype]

def get_analyzers() :

    return analyzers
