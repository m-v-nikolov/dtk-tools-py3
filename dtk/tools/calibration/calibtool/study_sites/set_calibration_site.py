import sys
import importlib

def set_calibration_site(cb, site) :
    # First try to import the site locally
    try:
        mod = importlib.import_module('.site_%s' % site,"study_sites")
    except:
        # The site couldnt get imported locally => fall back to the built-in
        mod = importlib.import_module('.site_' + site,"dtk.tools.calibration.calibtool.study_sites")
    setup_functions = mod.get_setup_functions()

    for fn in setup_functions:
        fn(cb)
    return {'_site_': site}

def get_reference_data(site, datatype) :
    # First try to import the site locally
    try:
        mod = importlib.import_module('.site_%s' % site,"study_sites")
    except:
        # The site couldnt get imported locally => fall back to the built-in
        mod = importlib.import_module('.site_' + site,"dtk.tools.calibration.calibtool.study_sites")
    return mod.load_reference_data(datatype)

def get_analyzers(site, analyzer) :
     # First try to import the site locally
    try:
        mod = importlib.import_module('.site_%s' % site,"study_sites")
    except:
        # The site couldnt get imported locally => fall back to the built-in
        mod = importlib.import_module('.site_' + site,"dtk.tools.calibration.calibtool.study_sites")
    return mod.get_analyzers(analyzer)
