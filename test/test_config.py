import unittest

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder


class TestConfigBuilder(unittest.TestCase):

    def setUp(self):
        self.cb = DTKConfigBuilder.from_defaults('MALARIA_SIM', Base_Air_Temperature=26)

    def test_kwargs(self):
        self.assertEqual(self.cb.get_param('Base_Air_Temperature'), 26)

    def test_enable_disable(self):
        self.cb.disable('Demographics_Birth')
        self.assertEqual(self.cb.get_param('Enable_Demographics_Birth'), 0)
        self.cb.enable('Demographics_Birth')
        self.assertEqual(self.cb.get_param('Enable_Demographics_Birth'), 1)

    def test_set_params(self):
        params = {
            "Falciparum_MSP_Variants":10,
            "CONFIG.Malaria_Drug_Params.Artemether.Fractional_Dose_By_Upper_Age.0.Fraction_Of_Adult_Dose":0.55,
            "VECTOR.arabiensis.Required_Habitat_Factor.CONSTANT":20000000,
            "VECTOR.funestus.Required_Habitat_Factor.0": 10000000,
            "DRUG.Artemether.Drug_Adherence_Rate":0.4,
            "HABSCALE.340461476":0.7,
            "CAMPAIGN.Input EIR intervention.Start_Day":33,
            "CAMPAIGN.0.Event_Coordinator_Config.Number_Repetitions":5
        }
        for (param,value) in params.iteritems():
            self.cb.set_param(param,value)

        self.assertEqual(self.cb.get_param("Falciparum_MSP_Variants"),10)
        self.assertEqual(self.cb.config["parameters"]["Malaria_Drug_Params"]["Artemether"]["Fractional_Dose_By_Upper_Age"][0]["Fraction_Of_Adult_Dose"],0.55)
        self.assertEqual(self.cb.config["parameters"]["Vector_Species_Params"]["arabiensis"]["Required_Habitat_Factor"][1],20000000)
        self.assertEqual(self.cb.config["parameters"]["Vector_Species_Params"]["funestus"]["Required_Habitat_Factor"][0],10000000)
        self.assertEqual(self.cb.config["parameters"]["Malaria_Drug_Params"]["Artemether"]["Drug_Adherence_Rate"],0.4)
        self.assertEqual(self.cb.config["parameters"]["HABSCALE.340461476"],0.7)
        self.assertEqual(self.cb.campaign["Events"][0]["Start_Day"],33)
        self.assertEqual(self.cb.campaign["Events"][0]["Event_Coordinator_Config"]["Number_Repetitions"],5)


class TestConfigExceptions(unittest.TestCase):

    def test_bad_kwargs(self):
        self.assertRaises(Exception, lambda: DTKConfigBuilder.from_defaults('MALARIA_SIM', Not_A_Climate_Parameter=26))

    def test_bad_simtype(self):
        self.assertRaises(Exception, lambda: DTKConfigBuilder.from_defaults('NOT_A_SIM'))    


if __name__ == '__main__':
    unittest.main()
