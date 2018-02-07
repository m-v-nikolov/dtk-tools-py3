from dtk.utils.Campaingn.CampaignHelper import BaseCampaign, update_attr
from dtk.utils.Campaingn.CampaignEnum import *


#################################
# Events and event coordinators
#################################

class CampaignEvent(BaseCampaign):
    def __init__(self, **kwargs):
        self.Event_Name = None                          # not listed
        self.Event_Coordinator_Config = {}
        self.Nodeset_Config = {}
        self.Start_Day = 1

        update_attr(self, **kwargs)


class CalendarEventCoordinator(BaseCampaign):
    def __init__(self, **kwargs):
        self.Demographic_Coverage = 1
        self.Distribution_Coverages = []                # array of floats
        self.Distribution_Times = []                    # array of floats
        self.Intervention_Config = {}
        self.Node_Property_Restrictions = []
        self.Property_Restrictions = []
        self.Property_Restrictions_Within_Node = []
        self.Target_Age_Max = 3.40E+38
        self.Target_Age_Min = 0
        self.Target_Demographic = Target_Demographic_Enum.Everyone
        self.Target_Gender = Target_Gender_Enum.All
        self.Target_Residents_Only = False              # bool: 0
        self.Timesteps_Between_Repetitions = -1

        update_attr(self, **kwargs)


class CommunityHealthWorkerEventCoordinator(BaseCampaign):
    def __init__(self, **kwargs):
        self.Amount_In_Shipment = 2.15E+09
        self.Days_Between_Shipments = 3.40E+38
        self.Demographic_Coverage = 1
        self.Duration = 3.40E+38
        self.Initial_Amount = 6
        self.Initial_Amount_Distribution_Type = Initial_Amount_Distribution_Type_Enum.NOT_INITIALIZED
        self.Initial_Amount_Max = 0
        self.Initial_Amount_Mean = 6
        self.Initial_Amount_Min = 0
        self.Initial_Amount_Std_Dev = 1
        self.Intervention_Config = {}
        self.Max_Distributed_Per_Day = 2.15E+09
        self.Max_Stock = 2.15E+09
        self.Node_Property_Restrictions = []
        self.Property_Restrictions = []
        self.Property_Restrictions_Within_Node = []
        self.Target_Age_Min = 0
        self.Target_Demographic = Target_Demographic_Enum.Everyone      # enum
        self.Target_Gender = Target_Gender_Enum.All                     # enum
        self.Target_Residents_Only = False                              # bool: 0
        self.Trigger_Condition_List = []
        self.Waiting_Period = 3.40E+38

        self.Distribution_Rate = 25                         # not listed

        update_attr(self, **kwargs)


class CoverageByNodeEventCoordinator(BaseCampaign):
    def __init__(self, **kwargs):
        self.Coverage_By_Node = []
        self.Demographic_Coverage = 1
        self.Intervention_Config = {}
        self.Node_Property_Restrictions = []
        self.Number_Repetitions = 1
        self.Property_Restrictions = []
        self.Property_Restrictions_Within_Node = []
        self.Target_Age_Min = 0
        self.Target_Demographic = Target_Demographic_Enum.Everyone
        self.Target_Gender = Target_Gender_Enum.All
        self.Target_Residents_Only = False              # bool: 0
        self.Timesteps_Between_Repetitions = -1

        update_attr(self, **kwargs)


class MultiInterventionEventCoordinator(BaseCampaign):
    def __init__(self, **kwargs):
        self.Demographic_Coverage = 1
        self.Intervention_Configs = []
        self.Node_Property_Restrictions = []
        self.Property_Restrictions = []
        self.Property_Restrictions_Within_Node = []
        self.Target_Age_Min = 0
        self.Target_Demographic = Target_Demographic_Enum.Everyone      # enum
        self.Target_Gender = Target_Gender_Enum.All
        self.Target_Residents_Only = False                              # bool: 0

        update_attr(self, **kwargs)


class NChooserEventCoordinator(BaseCampaign):
    def __init__(self, **kwargs):
        self.Age_Ranges_Years = []
        self.Distributions = []
        self.End_Day = 3.40E+38
        self.Intervention_Config = {}
        self.Max = 125
        self.Min = 0
        self.Num_Targeted = []
        self.Num_Targeted_Females = []
        self.Num_Targeted_Males = []
        self.Property_Restrictions_Within_Node = []
        self.Start_Day = 0

        update_attr(self, **kwargs)


class NodeEventCoordinator(BaseCampaign):
    def __init__(self, **kwargs):
        self.Intervention_Config = {}

        update_attr(self, **kwargs)


class SimpleDistributionEventCoordinator(BaseCampaign):
    def __init__(self, **kwargs):
        self.Coverage = 1
        self.Intervention_Config = {}

        update_attr(self, **kwargs)


class StandardInterventionDistributionEventCoordinator(BaseCampaign):
    def __init__(self, **kwargs):
        self.Demographic_Coverage = 1
        self.Intervention_Config = {}
        self.Node_Property_Restrictions = []
        self.Number_Repetitions = 1
        self.Property_Restrictions = []
        self.Property_Restrictions_Within_Node = []
        self.Target_Age_Max = 3.40E+38
        self.Target_Age_Min = 0
        self.Target_Demographic = Target_Demographic_Enum.Everyone
        self.Target_Gender = Target_Gender_Enum.All
        self.Target_Residents_Only = False                  # bool: 0
        self.Timesteps_Between_Repetitions = -1

        update_attr(self, **kwargs)



#################################
# Waning effect classes
#################################

class WaningEffectBox(BaseCampaign):
    def __init__(self, **kwargs):
        self.Box_Duration = 100
        self.Initial_Effect = -1

        update_attr(self, **kwargs)

class WaningEffectBoxExponential(BaseCampaign):
    def __init__(self, **kwargs):
        self.Box_Duration = 100
        self.Decay_Time_Constant = 100
        self.Initial_Effect = -1

        update_attr(self, **kwargs)

class WaningEffectConstant(BaseCampaign):
    def __init__(self, **kwargs):
        self.Expire_At_Durability_Map_End = 0       # not listed
        self.Initial_Effect = -1

        update_attr(self, **kwargs)

class WaningEffectExponential(BaseCampaign):
    def __init__(self, **kwargs):
        self.Box_Duration = 100                     # not listed
        self.Decay_Time_Constant = 100
        self.Initial_Effect = -1

        update_attr(self, **kwargs)


class WaningEffectMapLinear(BaseCampaign):
    """
        "Durability_Map": {
            "Times": [0, 385, 390, 10000],
            "Values": [0, 0.0, 0.5, 0.5]
        }
    """
    def __init__(self, **kwargs):
        self.Durability_Map = {}
        self.Expire_At_Durability_Map_End = False           # bool: 0
        self.Initial_Effect = -1
        self.Reference_Timer = 0
        self.Times = []
        self.Values = []

        update_attr(self, **kwargs)

class WaningEffectMapLinearAge(BaseCampaign):
    """
        "Durability_Map": {
            "Times": [0, 385, 390, 10000],
            "Values": [0, 0.0, 0.5, 0.5]
        }
    """
    def __init__(self, **kwargs):
        self.Durability_Map = {}
        self.Initial_Effect = -1
        self.Times = []
        self.Values = []

        update_attr(self, **kwargs)


class WaningEffectMapLinearSeasonal(BaseCampaign):
    """
        "Durability_Map": {
            "Times": [0, 385, 390, 10000],
            "Values": [0, 0.0, 0.5, 0.5]
        }
    """
    def __init__(self, **kwargs):
        self.Durability_Map = {}
        self.Initial_Effect = -1
        self.Times = []
        self.Values = []

        update_attr(self, **kwargs)


class WaningEffectMapPiecewise(BaseCampaign):
    """
        "Durability_Map": {
            "Times": [0, 385, 390, 10000],
            "Values": [0, 0.0, 0.5, 0.5]
        }
    """
    def __init__(self, **kwargs):
        self.Durability_Map = {}
        self.Expire_At_Durability_Map_End = False           # bool: 0
        self.Initial_Effect = -1
        self.Reference_Timer = 0
        self.Times = []
        self.Values = []

        update_attr(self, **kwargs)


class WaningEffectRandomBox(BaseCampaign):
    def __init__(self, **kwargs):
        self.Expected_Discard_Time = 100
        self.Initial_Effect = -1

        update_attr(self, **kwargs)




#################################
# Node-level interventions
#################################

class AnimalFeedKill(BaseCampaign):
    def __init__(self, **kwargs):
        self.Cost_To_Consumer = 10
        self.Disqualifying_Properties = None
        self.Intervention_Name = None
        self.Killing_Config = {}
        self.New_Property_Value = None

        update_attr(self, **kwargs)


class ArtificialDiet(BaseCampaign):
    def __init__(self, **kwargs):
        self.Artificial_Diet_Target = Artificial_Diet_Target_Enum.AD_WithinVillage      # enum
        self.Attraction_Config = {}
        self.Cost_To_Consumer = 10
        self.Disqualifying_Properties = None
        self.Intervention_Name = None
        self.New_Property_Value = None
        self.Primary_Decay_Time_Constant = 0
        self.Secondary_Decay_Time_Constant = 1

        update_attr(self, **kwargs)


class BirthTriggeredIV(BaseCampaign):
    def __init__(self, **kwargs):
        self.Actual_IndividualIntervention_Config = {}
        self.Demographic_Coverage = 1
        self.Disqualifying_Properties = None
        self.Duration = -1
        self.Intervention_Name = None
        self.New_Property_Value = None
        self.Property_Restrictions = {}
        self.Property_Restrictions_Within_Node = []
        self.Target_Age_Max = 3.40E+38
        self.Target_Demographic = Target_Demographic_Enum.Everyone
        self.Target_Gender = Target_Gender_Enum.All
        self.Target_Residents_Only = False              # bool: 0

        update_attr(self, **kwargs)


class ImportPressure(BaseCampaign):
    def __init__(self, **kwargs):
        self.Antigen = 0
        self.Daily_Import_Pressures = []                # array of floats
        self.Durations = 1                              # array of floats
        self.Genome = 0
        self.Import_Age = 365
        self.Incubation_Period_Override = -1
        self.Number_Cases_Per_Node = 1

        update_attr(self, **kwargs)


class InputEIR(BaseCampaign):
    def __init__(self, **kwargs):
        self.Age_Dependence = Age_Dependence_Enum.OFF         # enum
        self.Disqualifying_Properties = None
        self.Intervention_Name = None
        self.Monthly_EIR = []
        self.New_Property_Value = None

        update_attr(self, **kwargs)


class InsectKillingFence(BaseCampaign):
    def __init__(self, **kwargs):
        self.Cost_To_Consumer = 10
        self.Disqualifying_Properties = None
        self.Intervention_Name = None
        self.Killing_Config = {}
        self.New_Property_Value = None
        self.Primary_Decay_Time_Constant = 0
        self.Secondary_Decay_Time_Constant = 1

        update_attr(self, **kwargs)


class Larvicides(BaseCampaign):
    def __init__(self, **kwargs):
        self.Blocking_Config = {}
        self.Cost_To_Consumer = 10
        self.Disqualifying_Properties = None
        self.Habitat_Target = Habitat_Target_Enum.TEMPORARY_RAINFALL     # enum
        self.Intervention_Name = None
        self.Killing_Config = {}
        self.New_Property_Value = None
        self.Primary_Decay_Time_Constant = 0
        self.Secondary_Decay_Time_Constant = 1

        self.Reduction = 0                                      # not listed

        update_attr(self, **kwargs)



class MalariaChallenge(BaseCampaign):
    def __init__(self, **kwargs):
        self.Challenge_Type = None              # enum: InfectiousBites, Sporozoites
        self.Coverage = 1
        self.Disqualifying_Properties = None
        self.Infectious_Bite_Count = 1
        self.Intervention_Name = None
        self.New_Property_Value = None
        self.Sporozoite_Count = 1.00E+00

        update_attr(self, **kwargs)


class MigrateFamily(BaseCampaign):
    def __init__(self, **kwargs):
        self.Disqualifying_Properties = None
        self.Duration_At_Node_Distribution_Type = Duration_At_Node_Distribution_Type_Enum.NOT_INITIALIZED    # enum
        self.Duration_At_Node_Exponential_Period = 6
        self.Duration_At_Node_Fixed = 6
        self.Duration_At_Node_Gausian_Mean = 6
        self.Duration_At_Node_Gausian_StdDev = 1
        self.Duration_At_Node_Poisson_Mean = 6
        self.Duration_At_Node_Uniform_Max = 0
        self.Duration_At_Node_Uniform_Min = 0
        self.Duration_Before_Leaving_Distribution_Type = Duration_Before_Leaving_Distribution_Type_Enum.NOT_INITIALIZED  # enum
        self.Duration_Before_Leaving_Exponential_Period = 6
        self.Duration_Before_Leaving_Fixed = 6
        self.Duration_Before_Leaving_Gausian_Mean = 6
        self.Duration_Before_Leaving_Gausian_StdDev = 1
        self.Duration_Before_Leaving_Poisson_Mean = 6
        self.Duration_Before_Leaving_Uniform_Max = 0
        self.Duration_Before_Leaving_Uniform_Min = 0
        self.Intervention_Name = None
        self.Is_Moving = False                      # bool: 0
        self.New_Property_Value = None
        self.NodeID_To_Migrate_To = 0

        update_attr(self, **kwargs)


class MosquitoRelease(BaseCampaign):
    def __init__(self, **kwargs):
        self.Cost_To_Consumer = 0
        self.Disqualifying_Properties = None
        self.Dont_Allow_Duplicates = False                                    # bool: 0
        self.Intervention_Name = None
        self.Mated_Genetics = {}
        self.New_Property_Value = None
        self.Pesticide_Resistance = Pesticide_Resistance_Enum.WILD            # enum
        self.Released_Gender = None                                           # enum: VECTOR_FEMALE, VECTOR_MALE
        self.Released_Genetics = {}
        self.Released_Number = 10000
        self.Released_Species = None
        self.Released_Sterility = Released_Sterility_Enum.VECTOR_FERTILE      # enum
        self.Released_Wolbachia = Released_Wolbachia_Enum.WOLBACHIA_FREE      # enum

        update_attr(self, **kwargs)


class NodeLevelHealthTriggeredIV(BaseCampaign):
    def __init__(self, **kwargs):
        self.Actual_IndividualIntervention_Config = {}
        self.Actual_NodeIntervention_Config = {}
        self.Blackout_Event_Trigger = Campaign_Event_Enum.NoTrigger     # enum
        self.Blackout_On_First_Occurrence = False                       # bool: 0
        self.Blackout_Period = 0
        self.Demographic_Coverage = 1
        self.Disqualifying_Properties = None
        self.Distribute_On_Return_Home = 0
        self.Duration = -1
        self.Intervention_Name = None
        self.New_Property_Value = None
        self.Node_Property_Restrictions = []
        self.Property_Restrictions = []
        self.Property_Restrictions_Within_Node = []
        self.Target_Age_Max = 3.40E+38
        self.Target_Demographic = Target_Demographic_Enum.Everyone          # enum
        self.Target_Gender = Target_Gender_Enum.All                         # enum
        self.Target_Residents_Only = False                                  # bool: 0
        self.Trigger_Condition_List = []

        update_attr(self, **kwargs)


class NodeLevelHealthTriggeredIVScaleUpSwitch(BaseCampaign):
    def __init__(self, **kwargs):
        self.Actual_IndividualIntervention_Config = {}
        self.Actual_NodeIntervention_Config = {}
        self.Blackout_Event_Trigger = Campaign_Event_Enum.NoTrigger         # enum
        self.Blackout_On_First_Occurrence = False                           # bool: 0
        self.Blackout_Period = 0
        self.Demographic_Coverage = 1
        self.Demographic_Coverage_Time_Profile = Demographic_Coverage_Time_Profile_Enum.Immediate
        self.Disqualifying_Properties = None
        self.Distribute_On_Return_Home = False                              # bool: 0
        self.Duration = -1
        self.Initial_Demographic_Coverage = 0
        self.Intervention_Name = None
        self.New_Property_Value = None
        self.Node_Property_Restrictions = []
        self.Not_Covered_IndividualIntervention_Configs = []
        self.Primary_Time_Constant = 1
        self.Property_Restrictions = []
        self.Property_Restrictions_Within_Node = []
        self.Target_Age_Max = 3.40E+38
        self.Target_Demographic = Target_Demographic_Enum.Everyone             # enum
        self.Target_Gender = Target_Gender_Enum.All                            # enum
        self.Target_Residents_Only = False                                     # bool: 0
        self.Trigger_Condition_List = []

        self.Demographic_Coverage = 1                           # not listed
        self.Demographic_Coverage_Time_Profile = Demographic_Coverage_Time_Profile_Enum.Linear  # not listed

        update_attr(self, **kwargs)


class NodePropertyValueChanger(BaseCampaign):
    def __init__(self, **kwargs):
        self.Daily_Probability = 1
        self.Disqualifying_Properties = None
        self.Intervention_Name = None
        self.Maximum_Duration = 3.40E+38
        self.New_Property_Value = None
        self.Revert = 0
        self.Target_NP_Key_Value = None

        update_attr(self, **kwargs)


class Outbreak(BaseCampaign):
    def __init__(self, **kwargs):
        self.Antigen = 0
        self.Genome = 0
        self.Import_Age = 365
        self.Incubation_Period_Override = -1
        self.Number_Cases_Per_Node = 1

        update_attr(self, **kwargs)


class OutdoorRestKill(BaseCampaign):
    def __init__(self, **kwargs):
        self.Cost_To_Consumer = 10
        self.Disqualifying_Properties = None
        self.Intervention_Name = None
        self.Killing_Config = {}
        self.New_Property_Value = None
        self.Primary_Decay_Time_Constant = 0
        self.Secondary_Decay_Time_Constant = 1

        update_attr(self, **kwargs)


class OvipositionTrap(BaseCampaign):
    def __init__(self, **kwargs):
        self.Cost_To_Consumer = 10
        self.Disqualifying_Properties = None
        self.Habitat_Target = Habitat_Target_Enum.TEMPORARY_RAINFALL            # enum
        self.Intervention_Name = None
        self.Killing_Config = {}
        self.New_Property_Value = None
        self.Primary_Decay_Time_Constant = 0
        self.Secondary_Decay_Time_Constant = 1

        update_attr(self, **kwargs)


class ScaleLarvalHabitat(BaseCampaign):
    def __init__(self, **kwargs):
        self.Disqualifying_Properties = None
        self.Intervention_Name = None
        self.Larval_Habitat_Multiplier = {}
        self.New_Property_Value = None

        update_attr(self, **kwargs)


class SpaceSpraying(BaseCampaign):
    def __init__(self, **kwargs):
        self.Cost_To_Consumer = 10
        self.Disqualifying_Properties = None
        self.Habitat_Target = Habitat_Target_Enum.TEMPORARY_RAINFALL            # enum
        self.Intervention_Name = None
        self.Killing_Config = {}
        self.New_Property_Value = None
        self.Primary_Decay_Time_Constant = 0
        self.Reduction_Config = {}
        self.Secondary_Decay_Time_Constant = 1
        self.Spray_Kill_Target = Spray_Kill_Target_Enum.SpaceSpray_FemalesOnly   # enum

        self.Durability_Time_Profile = 'BOXDECAYDURABILITY'        # not listed. enum?

        update_attr(self, **kwargs)


class SpatialRepellent(BaseCampaign):
    def __init__(self, **kwargs):
        self.Cost_To_Consumer = 10
        self.Disqualifying_Properties = None
        self.Intervention_Name = None
        self.New_Property_Value = None
        self.Primary_Decay_Time_Constant = 0
        self.Repellency_Config = {}
        self.Secondary_Decay_Time_Constant = 1

        update_attr(self, **kwargs)


class SugarTrap(BaseCampaign):
    def __init__(self, **kwargs):
        self.Cost_To_Consumer = 10
        self.Disqualifying_Properties = None
        self.Intervention_Name = None
        self.Killing_Config = {}
        self.New_Property_Value = None
        self.Primary_Decay_Time_Constant = 0
        self.Secondary_Decay_Time_Constant = 1

        update_attr(self, **kwargs)




#################################
# Individual-level interventions
#################################

class AntimalarialDrug(BaseCampaign):
    def __init__(self, **kwargs):
        self.Cost_To_Consumer = 10
        self.Disqualifying_Properties = None
        self.Dont_Allow_Duplicates = False                  # bool: 0
        self.Dosing_Type = Dosing_Type_Enum.SingleDose      # enum
        self.Drug_Type = None                               # UNINITIALIZED STRING   enum:
        """
            Artemether_Lumefantrine
            Artemisinin
            Chloroquine
            GenPreerythrocytic
            GenTransBlocking
            Primaquine
            Quinine
            SP
            Tafenoquine
        """
        self.Intervention_Name = None
        self.New_Property_Value = None

        update_attr(self, **kwargs)


class ArtificialDietHousingModification(BaseCampaign):
    def __init__(self, **kwargs):
        self.Blocking_Config = {}
        self.Cost_To_Consumer = 8
        self.Disqualifying_Properties = None
        self.Dont_Allow_Duplicates = False              # bool: 0
        self.Intervention_Name = None
        self.Killing_Config = {}
        self.New_Property_Value = None

        update_attr(self, **kwargs)


class BroadcastEvent(BaseCampaign):
    def __init__(self, **kwargs):
        self.Broadcast_Event = Campaign_Event_Enum.NoTrigger        # enum type?
        self.Disqualifying_Properties = None
        self.Dont_Allow_Duplicates = False                     # bool: 0
        self.Intervention_Name = None
        self.New_Property_Value = None

        update_attr(self, **kwargs)


class BroadcastEventToOtherNodes(BaseCampaign):
    def __init__(self, **kwargs):
        self.Disqualifying_Properties = None
        self.Dont_Allow_Duplicates = False                  # bool: 0
        self.Event_Trigger = Campaign_Event_Enum.NoTrigger  # enum
        self.Include_My_Node = False                        # bool: 0
        self.Intervention_Name = None
        self.Max_Distance_To_Other_Nodes_Km = 3.40E+38
        self.New_Property_Value = None
        self.Node_Selection_Type = Node_Selection_Type_Enum.DISTANCE_ONLY       # enum

        update_attr(self, **kwargs)


class ControlledVaccine(BaseCampaign):
    def __init__(self, **kwargs):
        self.Cost_To_Consumer = 10
        self.Disqualifying_Properties = None
        self.Distributed_Event_Trigger = Campaign_Event_Enum.NoTrigger      # enum
        self.Dont_Allow_Duplicates = False                                  # bool: 0
        self.Duration_To_Wait_Before_Revaccination = 3.40E+38
        self.Efficacy_Is_Multiplicative = 1
        self.Expired_Event_Trigger = Campaign_Event_Enum.NoTrigger          # enum
        self.Intervention_Name = None
        self.New_Property_Value = None
        self.Vaccine_Take = 1
        self.Vaccine_Type = Vaccine_Type_Enum.Generic                       # enum
        self.Waning_Config = {}

        update_attr(self, **kwargs)


class DelayedIntervention(BaseCampaign):
    def __init__(self, **kwargs):
        self.Actual_IndividualIntervention_Configs = []
        self.Coverage = 1
        self.Delay_Distribution = Delay_Distribution_Enum.NOT_INITIALIZED       # enum
        self.Delay_Period = 6
        self.Delay_Period_Max = 6
        self.Delay_Period_Mean = 6
        self.Delay_Period_Min = 6
        self.Delay_Period_Scale = 16
        self.Delay_Period_Shape = 20
        self.Delay_Period_Std_Dev = 6
        self.Disqualifying_Properties = None
        self.Dont_Allow_Duplicates = False                  # bool: 0
        self.Intervention_Name = None
        self.New_Property_Value = None

        update_attr(self, **kwargs)


class HumanHostSeekingTrap(BaseCampaign):
    def __init__(self, **kwargs):
        self.Attract_Config = {}
        self.Cost_To_Consumer = 3.75
        self.Disqualifying_Properties = None
        self.Dont_Allow_Duplicates = False                  # bool: 0
        self.Intervention_Name = None
        self.Killing_Config = {}
        self.New_Property_Value = None
        self.Primary_Decay_Time_Constant = 0
        self.Secondary_Decay_Time_Constant = 1

        update_attr(self, **kwargs)


class IndividualImmunityChanger(BaseCampaign):
    def __init__(self, **kwargs):
        self.Boost_Acquire = 0
        self.Boost_Mortality = 0
        self.Boost_Threshold_Acquire = 0
        self.Boost_Threshold_Mortality = 0
        self.Boost_Threshold_Transmit = 0
        self.Boost_Transmit = 0
        self.Cost_To_Consumer = 10
        self.Prime_Acquire = 0
        self.Prime_Mortality = 0
        self.Prime_Transmit = 0

        update_attr(self, **kwargs)


class InsectKillingFenceHousingModification(BaseCampaign):
    def __init__(self, **kwargs):
        self.Blocking_Config = {}
        self.Cost_To_Consumer = 8
        self.Disqualifying_Properties = None
        self.Dont_Allow_Duplicates = False              # bool: 0
        self.Intervention_Name = None
        self.Killing_Config = {}
        self.New_Property_Value = None
        self.Primary_Decay_Time_Constant = 0
        self.Secondary_Decay_Time_Constant = 1

        update_attr(self, **kwargs)


class IRSHousingModification(BaseCampaign):
    def __init__(self, **kwargs):
        self.Blocking_Config = {}
        self.Cost_To_Consumer = 8
        self.Disqualifying_Properties = None
        self.Dont_Allow_Duplicates = False               # bool: 0
        self.Intervention_Name = None
        self.Killing_Config = {}
        self.New_Property_Value = None
        self.Primary_Decay_Time_Constant = 0
        self.Secondary_Decay_Time_Constant = 1

        update_attr(self, **kwargs)


class IVCalendar(BaseCampaign):
    def __init__(self, **kwargs):
        self.Actual_IndividualIntervention_Configs = []
        self.Age = None
        self.Calendar = []
        self.Disqualifying_Properties = None
        self.Dont_Allow_Duplicates = False              # bool: 0
        self.Dropout = False                            # bool: 0
        self.Intervention_Name = None
        self.New_Property_Value = None
        self.Probability = None

        update_attr(self, **kwargs)


class Ivermectin(BaseCampaign):
    def __init__(self, **kwargs):
        self.Cost_To_Consumer = 8
        self.Disqualifying_Properties = None
        self.Dont_Allow_Duplicates = False              # bool: 0
        self.Intervention_Name = None
        self.Killing_Config = {}
        self.New_Property_Value = None

        update_attr(self, **kwargs)


class MalariaDiagnostic(BaseCampaign):
    def __init__(self, **kwargs):
        self.Base_Sensitivity = 1
        self.Base_Specificity = 1
        self.Cost_To_Consumer = 1
        self.Days_To_Diagnosis = 0
        self.Detection_Threshold = 100
        self.Diagnostic_Type = Diagnostic_Type_Enum.Microscopy           # enum
        self.Disqualifying_Properties = None
        self.Dont_Allow_Duplicates = False                               # bool: 0
        self.Event_Or_Config = Event_Or_Config_Enum.Config               # enum
        self.Intervention_Name = None
        self.New_Property_Value = None
        self.Positive_Diagnosis_Config = {}
        self.Positive_Diagnosis_Event = Campaign_Event_Enum.NoTrigger    # enum
        self.Treatment_Fraction = 1

        update_attr(self, **kwargs)


class MigrateIndividuals(BaseCampaign):
    def __init__(self, **kwargs):
        self.Disqualifying_Properties = None
        self.Dont_Allow_Duplicates = False                                      # bool: 0
        self.Duration_At_Node_Distribution_Type = Duration_At_Node_Distribution_Type_Enum.NOT_INITIALIZED   # enum
        self.Duration_At_Node_Exponential_Period = 6
        self.Duration_At_Node_Fixed = 6
        self.Duration_At_Node_Gausian_Mean = 6
        self.Duration_At_Node_Gausian_StdDev = 1
        self.Duration_At_Node_Poisson_Mean = 6
        self.Duration_At_Node_Uniform_Max = 0
        self.Duration_At_Node_Uniform_Min = 0
        self.Duration_Before_Leaving_Distribution_Type = Duration_Before_Leaving_Distribution_Type_Enum.NOT_INITIALIZED     # enum
        self.Duration_Before_Leaving_Exponential_Period = 6
        self.Duration_Before_Leaving_Fixed = 6
        self.Duration_Before_Leaving_Gausian_Mean = 6
        self.Duration_Before_Leaving_Gausian_StdDev = 1
        self.Duration_Before_Leaving_Poisson_Mean = 6
        self.Duration_Before_Leaving_Uniform_Max = 0
        self.Duration_Before_Leaving_Uniform_Min = 0
        self.Intervention_Name = None
        self.Is_Moving = False                              # bool: 0
        self.New_Property_Value = None
        self.NodeID_To_Migrate_To = 0

        update_attr(self, **kwargs)


class MultiEffectBoosterVaccine(BaseCampaign):
    def __init__(self, **kwargs):
        self.Acquire_Config = {}
        self.Boost_Acquire = 0
        self.Boost_Mortality = 0
        self.Boost_Threshold_Acquire = 0
        self.Boost_Threshold_Mortality = 0
        self.Boost_Threshold_Transmit = 0
        self.Boost_Transmit = 0
        self.Cost_To_Consumer = 10
        self.Disqualifying_Properties = None
        self.Dont_Allow_Duplicates = False          # bool: 0
        self.Intervention_Name = None
        self.Mortality_Config = {}
        self.New_Property_Value = None
        self.Prime_Acquire = 0
        self.Prime_Mortality = 0
        self.Prime_Transmit = 0
        self.Transmit_Config = {}
        self.Vaccine_Take = 1

        update_attr(self, **kwargs)


class MultiEffectVaccine(BaseCampaign):
    def __init__(self, **kwargs):
        self.Acquire_Config = {}
        self.Cost_To_Consumer = 10
        self.Disqualifying_Properties = None
        self.Dont_Allow_Duplicates = False          # bool: 0
        self.Intervention_Name = None
        self.Mortality_Config = {}
        self.New_Property_Value = None
        self.Transmit_Config = {}
        self.Vaccine_Take = 1

        update_attr(self, **kwargs)


class MultiInterventionDistributor(BaseCampaign):
    def __init__(self, **kwargs):
        self.Disqualifying_Properties = None
        self.Dont_Allow_Duplicates = False           # bool: 0
        self.Intervention_List = []
        self.Intervention_Name = None
        self.New_Property_Value = None
        self.Number_Repetitions = 1
        self.Timesteps_Between_Repetitions = -1

        update_attr(self, **kwargs)


class OutbreakIndividual(BaseCampaign):
    def __init__(self, **kwargs):
        self.Antigen = 0
        self.Genome = 0
        self.Ignore_Immunity = True                 # bool: 1
        self.Incubation_Period_Override = -1

        update_attr(self, **kwargs)


class PropertyValueChanger(BaseCampaign):
    def __init__(self, **kwargs):
        self.Daily_Probability = 1
        self.Disqualifying_Properties = None
        self.Dont_Allow_Duplicates = False          # bool: 0
        self.Intervention_Name = None
        self.Maximum_Duration = 3.40E+38
        self.New_Property_Value = None
        self.Revert = 0
        self.Target_Property_Key = None
        self.Target_Property_Value = None

        update_attr(self, **kwargs)



class RTSSVaccine(BaseCampaign):
    def __init__(self, **kwargs):
        self.Antibody_Type = Antibody_Type_Enum.CSP                 # enum
        self.Antibody_Variant = 0
        self.Boosted_Antibody_Concentration = 1
        self.Cost_To_Consumer = 3.75
        self.Disqualifying_Properties = None
        self.Dont_Allow_Duplicates = False                          # bool: 0
        self.Intervention_Name = None
        self.New_Property_Value = None

        update_attr(self, **kwargs)


class ScreeningHousingModification(BaseCampaign):
    def __init__(self, **kwargs):
        self.Blocking_Config = {}
        self.Cost_To_Consumer = 8
        self.Disqualifying_Properties = None
        self.Dont_Allow_Duplicates = False                      # bool: 0
        self.Intervention_Name = None
        self.Killing_Config = {}
        self.New_Property_Value = None
        self.Primary_Decay_Time_Constant = 0
        self.Secondary_Decay_Time_Constant = 1

        update_attr(self, **kwargs)


class SimpleBednet(BaseCampaign):
    def __init__(self, **kwargs):
        self.Blocking_Config = {}
        self.Cost_To_Consumer = 3.75
        self.Disqualifying_Properties = None
        self.Dont_Allow_Duplicates = False          # bool: 0
        self.Intervention_Name = None
        self.Killing_Config = {}
        self.New_Property_Value = None
        self.Primary_Decay_Time_Constant = 0
        self.Secondary_Decay_Time_Constant = 1
        self.Usage_Config = {}

        self.Bednet_Type = None                     # is missing, NOT USED

        update_attr(self, **kwargs)


class SimpleBoosterVaccine(BaseCampaign):
    def __init__(self, **kwargs):
        self.Boost_Effect = 1
        self.Boost_Threshold = 0
        self.Cost_To_Consumer = 10
        self.Disqualifying_Properties = None
        self.Dont_Allow_Duplicates = False                      # bool: 0
        self.Efficacy_Is_Multiplicative = True                  # bool: 1
        self.Intervention_Name = None
        self.New_Property_Value = None
        self.Prime_Effect = 1
        self.Vaccine_Take = 1
        self.Vaccine_Type = Vaccine_Type_Enum.Generic           # enum
        self.Waning_Config = {}

        update_attr(self, **kwargs)



class SimpleDiagnostic(BaseCampaign):
    def __init__(self, **kwargs):
        self.Cost_To_Consumer = 1
        self.Days_To_Diagnosis = 0
        self.Disqualifying_Properties = None
        self.Dont_Allow_Duplicates = False                              # bool: 0
        self.Intervention_Name = None
        self.New_Property_Value = None
        self.Positive_Diagnosis_Config = {}
        self.Positive_Diagnosis_Event = Campaign_Event_Enum.NoTrigger   # enum
        self.Treatment_Fraction = 1

        update_attr(self, **kwargs)


class SimpleHealthSeekingBehavior(BaseCampaign):
    def __init__(self, **kwargs):
        self.Actual_IndividualIntervention_Config = {}
        self.Actual_IndividualIntervention_Event = Campaign_Event_Enum.NoTrigger     # enum
        self.Disqualifying_Properties = None
        self.Dont_Allow_Duplicates = False                          # bool: 0
        self.Event_Or_Config = Event_Or_Config_Enum.Config          # enum
        self.Intervention_Name = None
        self.New_Property_Value = None
        self.Single_Use = True                                      # bool: 1
        self.Tendency = 1

        update_attr(self, **kwargs)



class SimpleHousingModification(BaseCampaign):
    def __init__(self, **kwargs):
        self.Blocking_Config = {}
        self.Cost_To_Consumer = 8
        self.Disqualifying_Properties = None
        self.Dont_Allow_Duplicates = False          # bool: 0
        self.Intervention_Name = None
        self.Killing_Config = {}
        self.New_Property_Value = None

        update_attr(self, **kwargs)



class SimpleIndividualRepellent(BaseCampaign):
    def __init__(self, **kwargs):
        self.Blocking_Config = {}
        self.Cost_To_Consumer = 8
        self.Disqualifying_Properties = None
        self.Dont_Allow_Duplicates = False                  # bool: 0
        self.Intervention_Name = None
        self.New_Property_Value = None
        self.Primary_Decay_Time_Constant = 0
        self.Secondary_Decay_Time_Constant = 1

        update_attr(self, **kwargs)


class SimpleVaccine(BaseCampaign):
    def __init__(self, **kwargs):
        self.Cost_To_Consumer = 10
        self.Disqualifying_Properties = None
        self.Dont_Allow_Duplicates = False                  # bool: 0
        self.Efficacy_Is_Multiplicative = True              # bool: 1
        self.Event_Or_Config = Event_Or_Config_Enum.Config  # enum
        self.Intervention_Name = None
        self.New_Property_Value = None
        self.Vaccine_Take = 1
        self.Vaccine_Type = Vaccine_Type_Enum.Generic       # enum
        self.Waning_Config = {}

        update_attr(self, **kwargs)


class SpatialRepellentHousingModification(BaseCampaign):
    def __init__(self, **kwargs):
        self.Blocking_Config = {}
        self.Cost_To_Consumer = 8
        self.Disqualifying_Properties = None
        self.Dont_Allow_Duplicates = False                      # bool: 0
        self.Intervention_Name = None
        self.Killing_Config = {}
        self.New_Property_Value = None
        self.Primary_Decay_Time_Constant = 0
        self.Secondary_Decay_Time_Constant = 1

        update_attr(self, **kwargs)


class UsageDependentBednet(BaseCampaign):
    def __init__(self, **kwargs):
        self.Blocking_Config = {}
        self.Cost_To_Consumer = 3.75
        self.Discard_Event = Campaign_Event_Enum.NoTrigger          # enum
        self.Disqualifying_Properties = None
        self.Dont_Allow_Duplicates = False                          # bool: 0
        self.Expiration_Distribution_Type = Expiration_Distribution_Type_Enum.NOT_INITIALIZED      # enum
        self.Expiration_Percentage_Period_1 = 0.5
        self.Expiration_Period = 6.00E+00
        self.Expiration_Period_1 = 6
        self.Expiration_Period_2 = 6
        self.Expiration_Period_Max = 0
        self.Expiration_Period_Mean = 6
        self.Expiration_Period_Min = 0
        self.Expiration_Period_Std_Dev = 1
        self.Intervention_Name = None
        self.Killing_Config = {}
        self.New_Property_Value = None
        self.Received_Event = Campaign_Event_Enum.NoTrigger          # enum
        self.Usage_Config_List = None
        self.Using_Event = Campaign_Event_Enum.NoTrigger             # enum

        update_attr(self, **kwargs)






###################################
# Missing classes
###################################

class NodeSetNodeList(BaseCampaign):
    def __init__(self, **kwargs):
        self.Node_List = []

        update_attr(self, **kwargs)



class IncidenceEventCoordinator(BaseCampaign):
    def __init__(self, **kwargs):
        self.Incidence_Counter = None
        self.Number_Repetitions = 1000
        self.Responder = None
        self.Timesteps_Between_Repetitions = 30.0

        update_attr(self, **kwargs)


class NodeSetAll(BaseCampaign):
    def __init__(self, **kwargs):

        update_attr(self, **kwargs)



###################################
# Our classes
###################################

class Campaign(BaseCampaign):
    def __init__(self, **kwargs):
        self.Campaign_Name = "Empty Campaign"
        self.Use_Defaults = 1
        self.Events = []

        update_attr(self, **kwargs)

    def add_campaign_event(self):
        ce = CampaignEvent()
        self.Events.append(ce)







def list_all_classes():
    import sys
    import inspect
    from enum import Enum

    cm = campaign_modules = sys.modules[__name__]
    print('Type: ', type(cm))
    # print('length: ', len(cm))
    # print(cm)
    #
    # print(help(cm))
    # print('------------')
    # print(dir(cm))
    # print('------------')
    # print(cm.__dict__)

    print('--- List all classes ---')
    clsmembers = inspect.getmembers(cm, inspect.isclass)        # including included all enums
    print('Type: ', type(clsmembers))
    print('Length: ', len(clsmembers))
    print(clsmembers)

    # cls_dict = {k: v for k, v in clsmembers}
    # print(cls_dict)

    print('-----------')
    # cls_list = [k for k, v in clsmembers if issubclass(v, Enum) is False]
    # print(cls_list)
    cls_dict = {k: v for k, v in clsmembers if issubclass(v, Enum) is False}
    print('Type: ', type(cls_dict))
    print('Length: ', len(cls_dict))
    print(cls_dict)



def list_all_attr(aClass):
    """
    Note: seems not workikng
    :param aClass:
    :return:
    """

    # list all attributes
    an = aClass()
    attrs = vars(an)
    print(attrs)


if __name__ == "__main__":
    list_all_attr(Campaign)