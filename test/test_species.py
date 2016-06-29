import unittest

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
import dtk.vector.species as vs


class TestSpecies(unittest.TestCase):

    def setUp(self):
        self.cb = DTKConfigBuilder.from_defaults('VECTOR_SIM')

    def test_species_params(self):
        self.assertEqual(vs.get_species_param(self.cb, 'arabiensis', 'Immature_Duration'), 2)

        vs.set_species_param(self.cb, 'arabiensis', 'Egg_Batch_Size', 123)
        self.assertEqual(vs.get_species_param(self.cb, 'arabiensis', 'Egg_Batch_Size'), 123)

        vs.set_larval_habitat(self.cb, {'arabiensis': {'TEMPORARY_RAINFALL': 123, 'CONSTANT': 456}})
        self.assertDictEqual(vs.get_species_param(self.cb, 'arabiensis', 'Larval_Habitat_Types'),
                             {'TEMPORARY_RAINFALL': 123, 'CONSTANT': 456})

        vs.scale_all_habitats(self.cb, 2)
        self.assertDictEqual(vs.get_species_param(self.cb, 'arabiensis', 'Larval_Habitat_Types'),
                             {'TEMPORARY_RAINFALL': 246, 'CONSTANT': 912})

        farauti_swamp_habitat = vs.get_species_param(self.cb, 'funestus', 'Larval_Habitat_Types')['WATER_VEGETATION']
        self.assertEqual(farauti_swamp_habitat, 4e7)


if __name__ == '__main__':
    unittest.main()
