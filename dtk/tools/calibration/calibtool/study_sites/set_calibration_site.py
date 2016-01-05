import sys
import importlib

def set_calibration_site(cb, site) :

    sys.path.append('study_sites/')
    mod = importlib.import_module('site_' + site)
    setup_functions = mod.get_setup_functions()

    for fn in setup_functions:
        fn(cb)
    return {'_site_': site}

def get_reference_data(site, datatype) :

    sys.path.append('study_sites/')
    mod = importlib.import_module('site_' + site)
    return mod.load_reference_data(datatype)

def get_analyzers(site, analyzer) :

    sys.path.append('study_sites/')
    mod = importlib.import_module('site_' + site)
    return mod.get_analyzers(analyzer)
