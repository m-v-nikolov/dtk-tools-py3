import unittest

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
import dtk.tools.spatialworkflow.DemographicsGenerator as generator

class TestDemographicsGenerator(unittest.TestCase):
    """
    This test case covers the setting of arcsecond & degree resolution on a DemographicsGenerator object.
    """

    def setUp(self):
        self.cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')

    def test_generate_resolution_metadata(self):
        # test successful cases
        resolutions = set([None, generator.DemographicsGenerator.CUSTOM_RESOLUTION] +
                          generator.DemographicsGenerator.VALID_RESOLUTIONS.keys())

        # generate the expected results for comparison
        expected = {}
        for resolution in resolutions:
            if resolution is None:
                arcsec_res = generator.DemographicsGenerator.DEFAULT_RESOLUTION
                is_custom = False
            elif resolution is generator.DemographicsGenerator.CUSTOM_RESOLUTION:
                arcsec_res = generator.DemographicsGenerator.VALID_RESOLUTIONS[resolution]
                is_custom = True
            else:
                arcsec_res = resolution
                is_custom = False
            expected[resolution] = self.make_expected_dg_results(arcsec_res, is_custom)

        # test!
        for resolution in resolutions:
            dg = self.make_a_dg(resolution)

            # verifying DemographicsGenerator attributes
            self.assertEqual(dg.res_in_arcsec,     expected[resolution]['res_in_arcsec'])
            self.assertEqual(dg.custom_resolution, expected[resolution]['custom_resolution'])
            self.assertEqual(dg.res_in_degrees,    expected[resolution]['res_in_degrees'])

            # verifying generated metadata dict
            test_metadata = dg.generate_metadata()
            expected_metadata = expected[resolution]['metadata']
            for key in expected_metadata:
                self.assertTrue(key in test_metadata.keys())
                self.assertEqual(test_metadata[key], expected_metadata[key])
            self.assertEqual(type(test_metadata['Resolution']), int)

        # non-int convertible floating point and non-accepted integer resolutions should fail
        resolutions = [float(generator.DemographicsGenerator.DEFAULT_RESOLUTION)+0.01, 47]
        for resolution in resolutions:
            self.assertRaises(generator.InvalidResolution,
                              generator.DemographicsGenerator,
                              cb = self.cb,
                              nodes = [],
                              res_in_arcsec = resolution)

    def make_expected_dg_results(self, resolution, is_custom):
        return {
            "metadata": {
                "IdReference": "Gridded world grump%darcsec" % resolution,
                "Resolution": resolution
            },
            "res_in_arcsec": resolution,
            "custom_resolution": is_custom,
            "res_in_degrees": resolution / 3600.0
        }

    def make_a_dg(self, resolution):
        if resolution is None:
            dg = generator.DemographicsGenerator(cb=self.cb, nodes=[])
        else:
            dg = generator.DemographicsGenerator(cb=self.cb, nodes=[], res_in_arcsec=resolution)
        return dg

if __name__ == '__main__':
    unittest.main()