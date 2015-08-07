Adding a new malaria site or analyzer
-------------------------------------

Addition of a new site requires editing 3 scripts in calibtool.

In **load_settings.py**, add the new site name to
``settings['sites']``. Select from an existing analyzer, or see below on
adding a new analyzer. If the site shouldn't be weighted 1 relative to
other sites, note the weight of each analyzer for the site in
``settings['weight_by_site']``.

In **load_comparison_data.py**, add the reference data for the site to the
datastruct dictionary.

Malaria simulations with Edward's python tools also require setting up
simulation settings for each geography. A json file containing
information on each geography's config, campaign, and reporter
settings is specified in ``load_settings()``. In this file, add the new
site's information. If the new site uses a campaign other than input
EIR, health seeking, or challenge bite, a new line should be added to
``set_geographies_campaigns()`` in **geographies_calibration.py**.

Addition of a new analyzer requires editing at least 2 scripts and
writing one new script.

In **load_settings.py**, in ``load_analyzers()``, add setup info for the new
analyzer.

In **analyzers.py**, in ``analyze_malaria_sim()``, add an elif for the new
analyzer.

Write the new analyzer to be called from analyzers.py. The
LL_calculators.py script contains a variety of likelihood calculators
to be called, or a new one can be added if needed. The new analyzer
should return a log likelihood.

If visualizers are desired, add an elif to visualizer.py's
``visualize_malaria_sim()`` to call the new visualizer for the new
analyzer.

