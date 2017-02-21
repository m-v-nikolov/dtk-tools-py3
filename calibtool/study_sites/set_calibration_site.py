import importlib

from calibtool.CalibSite import CalibSite


def set_calibration_site(cb, site) :
    # For retrocompatibility, will accept site to be a string or an instance of CalibSite
    # If we get an instance of CalibSite then the name is in mod.name
    # TODO: Should remove the retrocompatibility and only accept CalibSite instance
    if not isinstance(site, CalibSite):
        # First try to import the site locally
        try:
            mod = importlib.import_module('.site_%s' % site, "study_sites")
        except:
            # The site couldnt get imported locally => fall back to the built-in
            mod = importlib.import_module('.site_' + site, "calibtool.study_sites")
    else:
        mod = site
        site = mod.name

    setup_functions = mod.get_setup_functions()

    for fn in setup_functions:
        fn(cb)
    return {'_site_': site}

def get_reference_data(site, datatype) :
    # First try to import the site locally
    try:
        mod = importlib.import_module('.site_%s' % site, "study_sites")
    except:
        # The site couldnt get imported locally => fall back to the built-in
        mod = importlib.import_module('.site_' + site, "calibtool.study_sites")
    return mod.load_reference_data(datatype)

def get_analyzers(site, analyzer) :
     # First try to import the site locally
    try:
        mod = importlib.import_module('.site_%s' % site, "study_sites")
    except:
        # The site couldnt get imported locally => fall back to the built-in
        mod = importlib.import_module('.site_' + site, "calibtool.study_sites")
    return mod.get_analyzers(analyzer)
