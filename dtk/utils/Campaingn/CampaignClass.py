import json
import os
import sys
import copy
from dtk.utils.Campaingn.CampaignHelper import BaseCampaign, update_attr
from dtk.utils.Campaingn.CampaignEnum import *


#################################
# Events and event coordinators
#################################

class CampaignEvent(BaseCampaign):
    def __init__(self, Event_Name=None, Event_Coordinator_Config={}, Nodeset_Config={}, Start_Day=1, **kwargs):
        self.Event_Name = Event_Name                                        # not listed
        self.Event_Coordinator_Config = Event_Coordinator_Config
        self.Nodeset_Config = Nodeset_Config
        self.Start_Day = Start_Day

        update_attr(self, **kwargs)


class CalendarEventCoordinator(BaseCampaign):
    def __init__(self, Demographic_Coverage=1, Distribution_Coverages=[], Distribution_Times=[],
                 Intervention_Config={}, Node_Property_Restrictions=[], Property_Restrictions=[],
                 Property_Restrictions_Within_Node=[], Target_Age_Max=3.4e+38, Target_Age_Min=0,
                 Target_Demographic=Target_Demographic_Enum.Everyone, Target_Gender=Target_Gender_Enum.All,
                 Target_Residents_Only=False, Timesteps_Between_Repetitions=-1, **kwargs):
        self.Demographic_Coverage = Demographic_Coverage
        self.Distribution_Coverages = Distribution_Coverages                # array of floats
        self.Distribution_Times = Distribution_Times                        # array of floats
        self.Intervention_Config = Intervention_Config
        self.Node_Property_Restrictions = Node_Property_Restrictions
        self.Property_Restrictions = Property_Restrictions
        self.Property_Restrictions_Within_Node = Property_Restrictions_Within_Node
        self.Target_Age_Max = Target_Age_Max
        self.Target_Age_Min = Target_Age_Min
        self.Target_Demographic = Target_Demographic
        self.Target_Gender = Target_Gender
        self.Target_Residents_Only = Target_Residents_Only                  # bool: 0
        self.Timesteps_Between_Repetitions = Timesteps_Between_Repetitions

        update_attr(self, **kwargs)


class CommunityHealthWorkerEventCoordinator(BaseCampaign):
    def __init__(self, Amount_In_Shipment=2150000000.0, Days_Between_Shipments=3.4e+38, Demographic_Coverage=1,
                 Duration=3.4e+38, Initial_Amount=6,
                 Initial_Amount_Distribution_Type=Initial_Amount_Distribution_Type_Enum.NOT_INITIALIZED,
                 Initial_Amount_Max=0, Initial_Amount_Mean=6, Initial_Amount_Min=0, Initial_Amount_Std_Dev=1,
                 Intervention_Config={}, Max_Distributed_Per_Day=2150000000.0, Max_Stock=2150000000.0,
                 Node_Property_Restrictions=[], Property_Restrictions=[], Property_Restrictions_Within_Node=[],
                 Target_Age_Min=0, Target_Demographic=Target_Demographic_Enum.Everyone,
                 Target_Gender=Target_Gender_Enum.All, Target_Residents_Only=False, Trigger_Condition_List=[],
                 Waiting_Period=3.4e+38, Distribution_Rate=25, **kwargs):
        self.Amount_In_Shipment = Amount_In_Shipment
        self.Days_Between_Shipments = Days_Between_Shipments
        self.Demographic_Coverage = Demographic_Coverage
        self.Duration = Duration
        self.Initial_Amount = Initial_Amount
        self.Initial_Amount_Distribution_Type = Initial_Amount_Distribution_Type
        self.Initial_Amount_Max = Initial_Amount_Max
        self.Initial_Amount_Mean = Initial_Amount_Mean
        self.Initial_Amount_Min = Initial_Amount_Min
        self.Initial_Amount_Std_Dev = Initial_Amount_Std_Dev
        self.Intervention_Config = Intervention_Config
        self.Max_Distributed_Per_Day = Max_Distributed_Per_Day
        self.Max_Stock = Max_Stock
        self.Node_Property_Restrictions = Node_Property_Restrictions
        self.Property_Restrictions = Property_Restrictions
        self.Property_Restrictions_Within_Node = Property_Restrictions_Within_Node
        self.Target_Age_Min = Target_Age_Min
        self.Target_Demographic = Target_Demographic            # enum
        self.Target_Gender = Target_Gender                      # enum
        self.Target_Residents_Only = Target_Residents_Only      # bool: 0
        self.Trigger_Condition_List = Trigger_Condition_List
        self.Waiting_Period = Waiting_Period

        self.Distribution_Rate = Distribution_Rate              # not listed

        update_attr(self, **kwargs)


class CoverageByNodeEventCoordinator(BaseCampaign):
    def __init__(self, Coverage_By_Node=[], Demographic_Coverage=1, Intervention_Config={},
                 Node_Property_Restrictions=[], Number_Repetitions=1, Property_Restrictions=[],
                 Property_Restrictions_Within_Node=[], Target_Age_Min=0,
                 Target_Demographic=Target_Demographic_Enum.Everyone, Target_Gender=Target_Gender_Enum.All,
                 Target_Residents_Only=False, Timesteps_Between_Repetitions=-1, **kwargs):
        self.Coverage_By_Node = Coverage_By_Node
        self.Demographic_Coverage = Demographic_Coverage
        self.Intervention_Config = Intervention_Config
        self.Node_Property_Restrictions = Node_Property_Restrictions
        self.Number_Repetitions = Number_Repetitions
        self.Property_Restrictions = Property_Restrictions
        self.Property_Restrictions_Within_Node = Property_Restrictions_Within_Node
        self.Target_Age_Min = Target_Age_Min
        self.Target_Demographic = Target_Demographic
        self.Target_Gender = Target_Gender
        self.Target_Residents_Only = Target_Residents_Only                  # bool: 0
        self.Timesteps_Between_Repetitions = Timesteps_Between_Repetitions

        update_attr(self, **kwargs)


class MultiInterventionEventCoordinator(BaseCampaign):
    def __init__(self, Demographic_Coverage=1, Intervention_Configs=[], Node_Property_Restrictions=[],
                 Property_Restrictions=[], Property_Restrictions_Within_Node=[], Target_Age_Min=0,
                 Target_Demographic=Target_Demographic_Enum.Everyone, Target_Gender=Target_Gender_Enum.All,
                 Target_Residents_Only=False, **kwargs):
        self.Demographic_Coverage = Demographic_Coverage
        self.Intervention_Configs = Intervention_Configs
        self.Node_Property_Restrictions = Node_Property_Restrictions
        self.Property_Restrictions = Property_Restrictions
        self.Property_Restrictions_Within_Node = Property_Restrictions_Within_Node
        self.Target_Age_Min = Target_Age_Min
        self.Target_Demographic = Target_Demographic                    # enum
        self.Target_Gender = Target_Gender
        self.Target_Residents_Only = Target_Residents_Only              # bool: 0

        update_attr(self, **kwargs)


class NChooserEventCoordinator(BaseCampaign):
    def __init__(self, Age_Ranges_Years=[], Distributions=[], End_Day=3.4e+38, Intervention_Config={},
                 Max=125, Min=0, Num_Targeted=[], Num_Targeted_Females=[], Num_Targeted_Males=[],
                 Property_Restrictions_Within_Node=[], Start_Day=0, **kwargs):
        self.Age_Ranges_Years = Age_Ranges_Years
        self.Distributions = Distributions
        self.End_Day = End_Day
        self.Intervention_Config = Intervention_Config
        self.Max = Max
        self.Min = Min
        self.Num_Targeted = Num_Targeted
        self.Num_Targeted_Females = Num_Targeted_Females
        self.Num_Targeted_Males = Num_Targeted_Males
        self.Property_Restrictions_Within_Node = Property_Restrictions_Within_Node
        self.Start_Day = Start_Day

        update_attr(self, **kwargs)


class NodeEventCoordinator(BaseCampaign):
    def __init__(self, Intervention_Config={}, **kwargs):
        self.Intervention_Config = Intervention_Config

        update_attr(self, **kwargs)


class SimpleDistributionEventCoordinator(BaseCampaign):
    def __init__(self, Coverage=1, Intervention_Config={}, **kwargs):
        self.Coverage = Coverage
        self.Intervention_Config = Intervention_Config

        update_attr(self, **kwargs)


class StandardInterventionDistributionEventCoordinator(BaseCampaign):
    def __init__(self, Demographic_Coverage=1, Intervention_Config={}, Node_Property_Restrictions=[],
                 Number_Repetitions=1, Property_Restrictions=[], Property_Restrictions_Within_Node=[],
                 Target_Age_Max=3.4e+38, Target_Age_Min=0, Target_Demographic=Target_Demographic_Enum.Everyone,
                 Target_Gender=Target_Gender_Enum.All, Target_Residents_Only=False,
                 Timesteps_Between_Repetitions=-1, **kwargs):
        self.Demographic_Coverage = Demographic_Coverage
        self.Intervention_Config = Intervention_Config
        self.Node_Property_Restrictions = Node_Property_Restrictions
        self.Number_Repetitions = Number_Repetitions
        self.Property_Restrictions = Property_Restrictions
        self.Property_Restrictions_Within_Node = Property_Restrictions_Within_Node
        self.Target_Age_Max = Target_Age_Max
        self.Target_Age_Min = Target_Age_Min
        self.Target_Demographic = Target_Demographic
        self.Target_Gender = Target_Gender
        self.Target_Residents_Only = Target_Residents_Only                  # bool: 0
        self.Timesteps_Between_Repetitions = Timesteps_Between_Repetitions

        update_attr(self, **kwargs)



#################################
# Waning effect classes
#################################

class WaningEffectBox(BaseCampaign):
    def __init__(self, Box_Duration=100, Initial_Effect=-1, **kwargs):
        self.Box_Duration = Box_Duration
        self.Initial_Effect = Initial_Effect

        update_attr(self, **kwargs)

class WaningEffectBoxExponential(BaseCampaign):
    def __init__(self, Box_Duration=100, Decay_Time_Constant=100, Initial_Effect=-1, **kwargs):
        self.Box_Duration = Box_Duration
        self.Decay_Time_Constant = Decay_Time_Constant
        self.Initial_Effect = Initial_Effect

        update_attr(self, **kwargs)

class WaningEffectConstant(BaseCampaign):
    def __init__(self, Expire_At_Durability_Map_End=0, Initial_Effect=-1, **kwargs):
        self.Expire_At_Durability_Map_End = Expire_At_Durability_Map_End        # not listed
        self.Initial_Effect = Initial_Effect

        update_attr(self, **kwargs)

class WaningEffectExponential(BaseCampaign):
    def __init__(self, Box_Duration=100, Decay_Time_Constant=100, Initial_Effect=-1, **kwargs):
        self.Box_Duration = Box_Duration                # not listed
        self.Decay_Time_Constant = Decay_Time_Constant
        self.Initial_Effect = Initial_Effect

        update_attr(self, **kwargs)


class WaningEffectMapLinear(BaseCampaign):
    """
        "Durability_Map": {
            "Times": [0, 385, 390, 10000],
            "Values": [0, 0.0, 0.5, 0.5]
        }
    """
    def __init__(self, Durability_Map={}, Expire_At_Durability_Map_End=False, Initial_Effect=-1,
                 Reference_Timer=0, Times=[], Values=[], **kwargs):
        self.Durability_Map = Durability_Map                # bool: 0
        self.Expire_At_Durability_Map_End = Expire_At_Durability_Map_End
        self.Initial_Effect = Initial_Effect
        self.Reference_Timer = Reference_Timer
        self.Times = Times
        self.Values = Values

        update_attr(self, **kwargs)


class WaningEffectMapLinearAge(BaseCampaign):
    """
        "Durability_Map": {
            "Times": [0, 385, 390, 10000],
            "Values": [0, 0.0, 0.5, 0.5]
        }
    """
    def __init__(self, Durability_Map={}, Initial_Effect=-1, Times=[], Values=[], **kwargs):
        self.Durability_Map = Durability_Map
        self.Initial_Effect = Initial_Effect
        self.Times = Times
        self.Values = Values

        update_attr(self, **kwargs)


class WaningEffectMapLinearSeasonal(BaseCampaign):
    """
        "Durability_Map": {
            "Times": [0, 385, 390, 10000],
            "Values": [0, 0.0, 0.5, 0.5]
        }
    """
    def __init__(self, Durability_Map={}, Initial_Effect=-1, Times=[], Values=[], **kwargs):
        self.Durability_Map = Durability_Map
        self.Initial_Effect = Initial_Effect
        self.Times = Times
        self.Values = Values

        update_attr(self, **kwargs)


class WaningEffectMapPiecewise(BaseCampaign):
    """
        "Durability_Map": {
            "Times": [0, 385, 390, 10000],
            "Values": [0, 0.0, 0.5, 0.5]
        }
    """
    def __init__(self, Durability_Map={}, Expire_At_Durability_Map_End=False, Initial_Effect=-1,
                 Reference_Timer=0, Times=[], Values=[], **kwargs):
        self.Durability_Map = Durability_Map
        self.Expire_At_Durability_Map_End = Expire_At_Durability_Map_End        # bool: 0
        self.Initial_Effect = Initial_Effect
        self.Reference_Timer = Reference_Timer
        self.Times = Times
        self.Values = Values

        update_attr(self, **kwargs)


class WaningEffectRandomBox(BaseCampaign):
    def __init__(self, Expected_Discard_Time=100, Initial_Effect=-1, **kwargs):
        self.Expected_Discard_Time = Expected_Discard_Time
        self.Initial_Effect = Initial_Effect

        update_attr(self, **kwargs)




#################################
# Node-level interventions
#################################

class AnimalFeedKill(BaseCampaign):
    def __init__(self, Cost_To_Consumer=10, Disqualifying_Properties=None, Intervention_Name=None,
                 Killing_Config={}, New_Property_Value=None, **kwargs):
        self.Cost_To_Consumer = Cost_To_Consumer
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Intervention_Name = Intervention_Name
        self.Killing_Config = Killing_Config
        self.New_Property_Value = New_Property_Value

        update_attr(self, **kwargs)


class ArtificialDiet(BaseCampaign):
    def __init__(self, Artificial_Diet_Target=Artificial_Diet_Target_Enum.AD_WithinVillage, Attraction_Config={},
                 Cost_To_Consumer=10, Disqualifying_Properties=None, Intervention_Name=None, New_Property_Value=None,
                 Primary_Decay_Time_Constant=0, Secondary_Decay_Time_Constant=1, **kwargs):
        self.Artificial_Diet_Target = Artificial_Diet_Target
        self.Attraction_Config = Attraction_Config
        self.Cost_To_Consumer = Cost_To_Consumer
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Intervention_Name = Intervention_Name
        self.New_Property_Value = New_Property_Value
        self.Primary_Decay_Time_Constant = Primary_Decay_Time_Constant
        self.Secondary_Decay_Time_Constant = Secondary_Decay_Time_Constant

        update_attr(self, **kwargs)


class BirthTriggeredIV(BaseCampaign):
    def __init__(self, Actual_IndividualIntervention_Config={}, Demographic_Coverage=1, Disqualifying_Properties=None,
                 Duration=-1, Intervention_Name=None, New_Property_Value=None, Property_Restrictions={},
                 Property_Restrictions_Within_Node=[], Target_Age_Max=3.4e+38,
                 Target_Demographic=Target_Demographic_Enum.Everyone, Target_Gender=Target_Gender_Enum.All,
                 Target_Residents_Only=False, **kwargs):
        self.Actual_IndividualIntervention_Config = Actual_IndividualIntervention_Config
        self.Demographic_Coverage = Demographic_Coverage
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Duration = Duration
        self.Intervention_Name = Intervention_Name
        self.New_Property_Value = New_Property_Value
        self.Property_Restrictions = Property_Restrictions
        self.Property_Restrictions_Within_Node = Property_Restrictions_Within_Node
        self.Target_Age_Max = Target_Age_Max
        self.Target_Demographic = Target_Demographic
        self.Target_Gender = Target_Gender
        self.Target_Residents_Only = Target_Residents_Only      # bool: 0

        update_attr(self, **kwargs)


class ImportPressure(BaseCampaign):
    def __init__(self, Antigen=0, Daily_Import_Pressures=[], Durations=1, Genome=0, Import_Age=365,
                 Incubation_Period_Override=-1, Number_Cases_Per_Node=1, **kwargs):
        self.Antigen = Antigen
        self.Daily_Import_Pressures = Daily_Import_Pressures            # array of floats
        self.Durations = Durations                                      # [TODO]: array of floats
        self.Genome = Genome
        self.Import_Age = Import_Age
        self.Incubation_Period_Override = Incubation_Period_Override
        self.Number_Cases_Per_Node = Number_Cases_Per_Node

        update_attr(self, **kwargs)


class InputEIR(BaseCampaign):
    def __init__(self, Age_Dependence=Age_Dependence_Enum.OFF, Disqualifying_Properties=None,
                 Intervention_Name=None, Monthly_EIR=[], New_Property_Value=None, **kwargs):
        self.Age_Dependence = Age_Dependence                    # enum
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Intervention_Name = Intervention_Name
        self.Monthly_EIR = Monthly_EIR
        self.New_Property_Value = New_Property_Value

        update_attr(self, **kwargs)


class InsectKillingFence(BaseCampaign):
    def __init__(self, Cost_To_Consumer=10, Disqualifying_Properties=None, Intervention_Name=None,
                 Killing_Config={}, New_Property_Value=None, Primary_Decay_Time_Constant=0,
                 Secondary_Decay_Time_Constant=1, **kwargs):
        self.Cost_To_Consumer = Cost_To_Consumer
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Intervention_Name = Intervention_Name
        self.Killing_Config = Killing_Config
        self.New_Property_Value = New_Property_Value
        self.Primary_Decay_Time_Constant = Primary_Decay_Time_Constant
        self.Secondary_Decay_Time_Constant = Secondary_Decay_Time_Constant

        update_attr(self, **kwargs)


class Larvicides(BaseCampaign):
    def __init__(self, Blocking_Config={}, Cost_To_Consumer=10, Disqualifying_Properties=None,
                 Habitat_Target=Habitat_Target_Enum.TEMPORARY_RAINFALL, Intervention_Name=None,
                 Killing_Config={}, New_Property_Value=None, Primary_Decay_Time_Constant=0,
                 Secondary_Decay_Time_Constant=1, Reduction=0, **kwargs):
        self.Blocking_Config = Blocking_Config
        self.Cost_To_Consumer = Cost_To_Consumer
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Habitat_Target = Habitat_Target                                # enum
        self.Intervention_Name = Intervention_Name
        self.Killing_Config = Killing_Config
        self.New_Property_Value = New_Property_Value
        self.Primary_Decay_Time_Constant = Primary_Decay_Time_Constant
        self.Secondary_Decay_Time_Constant = Secondary_Decay_Time_Constant

        self.Reduction = Reduction                                          # not listed

        update_attr(self, **kwargs)


class MalariaChallenge(BaseCampaign):
    def __init__(self, Challenge_Type=None, Coverage=1, Disqualifying_Properties=None, Infectious_Bite_Count=1,
                 Intervention_Name=None, New_Property_Value=None, Sporozoite_Count=1.0, **kwargs):
        self.Challenge_Type = Challenge_Type        # [TODO]: enum: InfectiousBites, Sporozoites
        self.Coverage = Coverage
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Infectious_Bite_Count = Infectious_Bite_Count
        self.Intervention_Name = Intervention_Name
        self.New_Property_Value = New_Property_Value
        self.Sporozoite_Count = Sporozoite_Count

        update_attr(self, **kwargs)


class MigrateFamily(BaseCampaign):
    def __init__(self, Disqualifying_Properties=None,
                 Duration_At_Node_Distribution_Type=Duration_At_Node_Distribution_Type_Enum.NOT_INITIALIZED,
                 Duration_At_Node_Exponential_Period=6, Duration_At_Node_Fixed=6, Duration_At_Node_Gausian_Mean=6,
                 Duration_At_Node_Gausian_StdDev=1, Duration_At_Node_Poisson_Mean=6, Duration_At_Node_Uniform_Max=0,
                 Duration_At_Node_Uniform_Min=0,
                 Duration_Before_Leaving_Distribution_Type=Duration_Before_Leaving_Distribution_Type_Enum.NOT_INITIALIZED,
                 Duration_Before_Leaving_Exponential_Period=6, Duration_Before_Leaving_Fixed=6,
                 Duration_Before_Leaving_Gausian_Mean=6, Duration_Before_Leaving_Gausian_StdDev=1,
                 Duration_Before_Leaving_Poisson_Mean=6, Duration_Before_Leaving_Uniform_Max=0,
                 Duration_Before_Leaving_Uniform_Min=0, Intervention_Name=None, Is_Moving=False,
                 New_Property_Value=None, NodeID_To_Migrate_To=0, **kwargs):
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Duration_At_Node_Distribution_Type = Duration_At_Node_Distribution_Type                    # enum
        self.Duration_At_Node_Exponential_Period = Duration_At_Node_Exponential_Period
        self.Duration_At_Node_Fixed = Duration_At_Node_Fixed
        self.Duration_At_Node_Gausian_Mean = Duration_At_Node_Gausian_Mean
        self.Duration_At_Node_Gausian_StdDev = Duration_At_Node_Gausian_StdDev
        self.Duration_At_Node_Poisson_Mean = Duration_At_Node_Poisson_Mean
        self.Duration_At_Node_Uniform_Max = Duration_At_Node_Uniform_Max
        self.Duration_At_Node_Uniform_Min = Duration_At_Node_Uniform_Min
        self.Duration_Before_Leaving_Distribution_Type = Duration_Before_Leaving_Distribution_Type      # enum
        self.Duration_Before_Leaving_Exponential_Period = Duration_Before_Leaving_Exponential_Period
        self.Duration_Before_Leaving_Fixed = Duration_Before_Leaving_Fixed
        self.Duration_Before_Leaving_Gausian_Mean = Duration_Before_Leaving_Gausian_Mean
        self.Duration_Before_Leaving_Gausian_StdDev = Duration_Before_Leaving_Gausian_StdDev
        self.Duration_Before_Leaving_Poisson_Mean = Duration_Before_Leaving_Poisson_Mean
        self.Duration_Before_Leaving_Uniform_Max = Duration_Before_Leaving_Uniform_Max
        self.Duration_Before_Leaving_Uniform_Min = Duration_Before_Leaving_Uniform_Min
        self.Intervention_Name = Intervention_Name
        self.Is_Moving = Is_Moving                                                                      # bool: 0
        self.New_Property_Value = New_Property_Value
        self.NodeID_To_Migrate_To = NodeID_To_Migrate_To

        update_attr(self, **kwargs)


class MosquitoRelease(BaseCampaign):
    def __init__(self, Cost_To_Consumer=0, Disqualifying_Properties=None, Dont_Allow_Duplicates=False,
                 Intervention_Name=None, Mated_Genetics={}, New_Property_Value=None,
                 Pesticide_Resistance=Pesticide_Resistance_Enum.WILD, Released_Gender=None,
                 Released_Genetics={}, Released_Number=10000, Released_Species=None,
                 Released_Sterility=Released_Sterility_Enum.VECTOR_FERTILE,
                 Released_Wolbachia=Released_Wolbachia_Enum.WOLBACHIA_FREE, **kwargs):
        self.Cost_To_Consumer = Cost_To_Consumer
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Dont_Allow_Duplicates = Dont_Allow_Duplicates                      # bool: 0
        self.Intervention_Name = Intervention_Name
        self.Mated_Genetics = Mated_Genetics                                    # [TODO]: enum: VECTOR_FEMALE, VECTOR_MALE
        self.New_Property_Value = New_Property_Value
        self.Pesticide_Resistance = Pesticide_Resistance                        # enum
        self.Released_Gender = Released_Gender
        self.Released_Genetics = Released_Genetics
        self.Released_Number = Released_Number
        self.Released_Species = Released_Species
        self.Released_Sterility = Released_Sterility                            # enum
        self.Released_Wolbachia = Released_Wolbachia                            # enum

        update_attr(self, **kwargs)


class NodeLevelHealthTriggeredIV(BaseCampaign):
    def __init__(self, Actual_IndividualIntervention_Config={}, Actual_NodeIntervention_Config={},
                 Blackout_Event_Trigger=Campaign_Event_Enum.NoTrigger, Blackout_On_First_Occurrence=False,
                 Blackout_Period=0, Demographic_Coverage=1, Disqualifying_Properties=None,
                 Distribute_On_Return_Home=0, Duration=-1, Intervention_Name=None, New_Property_Value=None,
                 Node_Property_Restrictions=[], Property_Restrictions=[], Property_Restrictions_Within_Node=[],
                 Target_Age_Max=3.4e+38, Target_Demographic=Target_Demographic_Enum.Everyone,
                 Target_Gender=Target_Gender_Enum.All, Target_Residents_Only=False,
                 Trigger_Condition_List=[], **kwargs):
        self.Actual_IndividualIntervention_Config = Actual_IndividualIntervention_Config
        self.Actual_NodeIntervention_Config = Actual_NodeIntervention_Config
        self.Blackout_Event_Trigger = Blackout_Event_Trigger                # enum
        self.Blackout_On_First_Occurrence = Blackout_On_First_Occurrence    # bool: 0
        self.Blackout_Period = Blackout_Period
        self.Demographic_Coverage = Demographic_Coverage
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Distribute_On_Return_Home = Distribute_On_Return_Home
        self.Duration = Duration
        self.Intervention_Name = Intervention_Name
        self.New_Property_Value = New_Property_Value
        self.Node_Property_Restrictions = Node_Property_Restrictions
        self.Property_Restrictions = Property_Restrictions
        self.Property_Restrictions_Within_Node = Property_Restrictions_Within_Node
        self.Target_Age_Max = Target_Age_Max
        self.Target_Demographic = Target_Demographic                    # enum
        self.Target_Gender = Target_Gender                              # enum
        self.Target_Residents_Only = Target_Residents_Only              # bool: 0
        self.Trigger_Condition_List = Trigger_Condition_List

        update_attr(self, **kwargs)


class NodeLevelHealthTriggeredIVScaleUpSwitch(BaseCampaign):
    def __init__(self, Actual_IndividualIntervention_Config={}, Actual_NodeIntervention_Config={},
                 Blackout_Event_Trigger=Campaign_Event_Enum.NoTrigger, Blackout_On_First_Occurrence=False,
                 Blackout_Period=0, Demographic_Coverage=1,
                 Demographic_Coverage_Time_Profile=Demographic_Coverage_Time_Profile_Enum.Linear,
                 Disqualifying_Properties=None, Distribute_On_Return_Home=False, Duration=-1,
                 Initial_Demographic_Coverage=0, Intervention_Name=None, New_Property_Value=None,
                 Node_Property_Restrictions=[], Not_Covered_IndividualIntervention_Configs=[],
                 Primary_Time_Constant=1, Property_Restrictions=[], Property_Restrictions_Within_Node=[],
                 Target_Age_Max=3.4e+38, Target_Demographic=Target_Demographic_Enum.Everyone,
                 Target_Gender=Target_Gender_Enum.All, Target_Residents_Only=False, Trigger_Condition_List=[],
                 **kwargs):
        self.Actual_IndividualIntervention_Config = Actual_IndividualIntervention_Config
        self.Actual_NodeIntervention_Config = Actual_NodeIntervention_Config
        self.Blackout_Event_Trigger = Blackout_Event_Trigger                                            # enum
        self.Blackout_On_First_Occurrence = Blackout_On_First_Occurrence                                # bool: 0
        self.Blackout_Period = Blackout_Period
        self.Demographic_Coverage = Demographic_Coverage                                                # not listed
        self.Demographic_Coverage_Time_Profile = Demographic_Coverage_Time_Profile                      # not listed
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Distribute_On_Return_Home = Distribute_On_Return_Home                                      # bool: 0
        self.Duration = Duration
        self.Initial_Demographic_Coverage = Initial_Demographic_Coverage
        self.Intervention_Name = Intervention_Name
        self.New_Property_Value = New_Property_Value
        self.Node_Property_Restrictions = Node_Property_Restrictions
        self.Not_Covered_IndividualIntervention_Configs = Not_Covered_IndividualIntervention_Configs
        self.Primary_Time_Constant = Primary_Time_Constant
        self.Property_Restrictions = Property_Restrictions
        self.Property_Restrictions_Within_Node = Property_Restrictions_Within_Node
        self.Target_Age_Max = Target_Age_Max
        self.Target_Demographic = Target_Demographic                        # enum
        self.Target_Gender = Target_Gender                                  # enum
        self.Target_Residents_Only = Target_Residents_Only                  # bool: 0
        self.Trigger_Condition_List = Trigger_Condition_List

        update_attr(self, **kwargs)


class NodePropertyValueChanger(BaseCampaign):
    def __init__(self, Daily_Probability=1, Disqualifying_Properties=None, Intervention_Name=None,
                 Maximum_Duration=3.4e+38, New_Property_Value=None, Revert=0, Target_NP_Key_Value=None,
                 **kwargs):
        self.Daily_Probability = Daily_Probability
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Intervention_Name = Intervention_Name
        self.Maximum_Duration = Maximum_Duration
        self.New_Property_Value = New_Property_Value
        self.Revert = Revert
        self.Target_NP_Key_Value = Target_NP_Key_Value

        update_attr(self, **kwargs)


class Outbreak(BaseCampaign):
    def __init__(self, Antigen=0, Genome=0, Import_Age=365, Incubation_Period_Override=-1,
                 Number_Cases_Per_Node=1, **kwargs):
        self.Antigen = Antigen
        self.Genome = Genome
        self.Import_Age = Import_Age
        self.Incubation_Period_Override = Incubation_Period_Override
        self.Number_Cases_Per_Node = Number_Cases_Per_Node

        update_attr(self, **kwargs)


class OutdoorRestKill(BaseCampaign):
    def __init__(self, Cost_To_Consumer=10, Disqualifying_Properties=None, Intervention_Name=None,
                 Killing_Config={}, New_Property_Value=None, Primary_Decay_Time_Constant=0,
                 Secondary_Decay_Time_Constant=1, **kwargs):
        self.Cost_To_Consumer = Cost_To_Consumer
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Intervention_Name = Intervention_Name
        self.Killing_Config = Killing_Config
        self.New_Property_Value = New_Property_Value
        self.Primary_Decay_Time_Constant = Primary_Decay_Time_Constant
        self.Secondary_Decay_Time_Constant = Secondary_Decay_Time_Constant

        update_attr(self, **kwargs)


class OvipositionTrap(BaseCampaign):
    def __init__(self, Cost_To_Consumer=10, Disqualifying_Properties=None,
                 Habitat_Target=Habitat_Target_Enum.TEMPORARY_RAINFALL, Intervention_Name=None,
                 Killing_Config={}, New_Property_Value=None, Primary_Decay_Time_Constant=0,
                 Secondary_Decay_Time_Constant=1, **kwargs):
        self.Cost_To_Consumer = Cost_To_Consumer
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Habitat_Target = Habitat_Target                                # enum
        self.Intervention_Name = Intervention_Name
        self.Killing_Config = Killing_Config
        self.New_Property_Value = New_Property_Value
        self.Primary_Decay_Time_Constant = Primary_Decay_Time_Constant
        self.Secondary_Decay_Time_Constant = Secondary_Decay_Time_Constant

        update_attr(self, **kwargs)


class ScaleLarvalHabitat(BaseCampaign):
    def __init__(self, Disqualifying_Properties=None, Intervention_Name=None, Larval_Habitat_Multiplier={},
                 New_Property_Value=None, **kwargs):
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Intervention_Name = Intervention_Name
        self.Larval_Habitat_Multiplier = Larval_Habitat_Multiplier
        self.New_Property_Value = New_Property_Value

        update_attr(self, **kwargs)


class SpaceSpraying(BaseCampaign):
    def __init__(self, Cost_To_Consumer=10, Disqualifying_Properties=None,
                 Habitat_Target=Habitat_Target_Enum.TEMPORARY_RAINFALL, Intervention_Name=None,
                 Killing_Config={}, New_Property_Value=None, Primary_Decay_Time_Constant=0,
                 Reduction_Config={}, Secondary_Decay_Time_Constant=1,
                 Spray_Kill_Target=Spray_Kill_Target_Enum.SpaceSpray_FemalesOnly,
                 Durability_Time_Profile='BOXDECAYDURABILITY', **kwargs):
        self.Cost_To_Consumer = Cost_To_Consumer
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Habitat_Target = Habitat_Target                                    # enum
        self.Intervention_Name = Intervention_Name
        self.Killing_Config = Killing_Config
        self.New_Property_Value = New_Property_Value
        self.Primary_Decay_Time_Constant = Primary_Decay_Time_Constant
        self.Reduction_Config = Reduction_Config
        self.Secondary_Decay_Time_Constant = Secondary_Decay_Time_Constant
        self.Spray_Kill_Target = Spray_Kill_Target                               # enum
        self.Durability_Time_Profile = Durability_Time_Profile                   # 'BOXDECAYDURABILITY'        # not listed. enum?

        update_attr(self, **kwargs)


class SpatialRepellent(BaseCampaign):
    def __init__(self, Cost_To_Consumer=10, Disqualifying_Properties=None, Intervention_Name=None,
                 New_Property_Value=None, Primary_Decay_Time_Constant=0, Repellency_Config={},
                 Secondary_Decay_Time_Constant=1, **kwargs):
        self.Cost_To_Consumer = Cost_To_Consumer
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Intervention_Name = Intervention_Name
        self.New_Property_Value = New_Property_Value
        self.Primary_Decay_Time_Constant = Primary_Decay_Time_Constant
        self.Repellency_Config = Repellency_Config
        self.Secondary_Decay_Time_Constant = Secondary_Decay_Time_Constant

        update_attr(self, **kwargs)


class SugarTrap(BaseCampaign):
    def __init__(self, Cost_To_Consumer=10, Disqualifying_Properties=None, Intervention_Name=None,
                 Killing_Config={}, New_Property_Value=None, Primary_Decay_Time_Constant=0,
                 Secondary_Decay_Time_Constant=1, **kwargs):
        self.Cost_To_Consumer = Cost_To_Consumer
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Intervention_Name = Intervention_Name
        self.Killing_Config = Killing_Config
        self.New_Property_Value = New_Property_Value
        self.Primary_Decay_Time_Constant = Primary_Decay_Time_Constant
        self.Secondary_Decay_Time_Constant = Secondary_Decay_Time_Constant

        update_attr(self, **kwargs)




#################################
# Individual-level interventions
#################################

class AntimalarialDrug(BaseCampaign):
    def __init__(self, Cost_To_Consumer=10, Disqualifying_Properties=None, Dont_Allow_Duplicates=False,
                 Dosing_Type=Dosing_Type_Enum.SingleDose, Drug_Type=None, Intervention_Name=None,
                 New_Property_Value=None, **kwargs):
        self.Cost_To_Consumer = Cost_To_Consumer
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Dont_Allow_Duplicates = Dont_Allow_Duplicates          # bool: 0
        self.Dosing_Type = Dosing_Type                              # enum
        self.Drug_Type = Drug_Type                                  # UNINITIALIZED STRING   enum:
        self.Intervention_Name = Intervention_Name
        self.New_Property_Value = New_Property_Value

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

        update_attr(self, **kwargs)


class ArtificialDietHousingModification(BaseCampaign):
    def __init__(self, Blocking_Config={}, Cost_To_Consumer=8, Disqualifying_Properties=None,
                 Dont_Allow_Duplicates=False, Intervention_Name=None, Killing_Config={},
                 New_Property_Value=None, **kwargs):
        self.Blocking_Config = Blocking_Config
        self.Cost_To_Consumer = Cost_To_Consumer
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Dont_Allow_Duplicates = Dont_Allow_Duplicates          # bool: 0
        self.Intervention_Name = Intervention_Name
        self.Killing_Config = Killing_Config
        self.New_Property_Value = New_Property_Value

        update_attr(self, **kwargs)


class BroadcastEvent(BaseCampaign):
    def __init__(self, Broadcast_Event=Campaign_Event_Enum.NoTrigger, Disqualifying_Properties=None,
                 Dont_Allow_Duplicates=False, Intervention_Name=None, New_Property_Value=None,
                 **kwargs):
        self.Broadcast_Event = Broadcast_Event                      # enum type?
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Dont_Allow_Duplicates = Dont_Allow_Duplicates          # bool: 0
        self.Intervention_Name = Intervention_Name
        self.New_Property_Value = New_Property_Value

        update_attr(self, **kwargs)


class BroadcastEventToOtherNodes(BaseCampaign):
    def __init__(self, Disqualifying_Properties=None, Dont_Allow_Duplicates=False,
                 Event_Trigger=Campaign_Event_Enum.NoTrigger, Include_My_Node=False,
                 Intervention_Name=None, Max_Distance_To_Other_Nodes_Km=3.4e+38, New_Property_Value=None,
                 Node_Selection_Type=Node_Selection_Type_Enum.DISTANCE_ONLY, **kwargs):
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Dont_Allow_Duplicates = Dont_Allow_Duplicates  # bool: 0
        self.Event_Trigger = Event_Trigger                  # enum
        self.Include_My_Node = Include_My_Node              # bool: 0
        self.Intervention_Name = Intervention_Name
        self.Max_Distance_To_Other_Nodes_Km = Max_Distance_To_Other_Nodes_Km
        self.New_Property_Value = New_Property_Value
        self.Node_Selection_Type = Node_Selection_Type      # bool: 0

        update_attr(self, **kwargs)


class ControlledVaccine(BaseCampaign):
    def __init__(self, Cost_To_Consumer=10, Disqualifying_Properties=None,
                 Distributed_Event_Trigger=Campaign_Event_Enum.NoTrigger, Dont_Allow_Duplicates=False,
                 Duration_To_Wait_Before_Revaccination=3.4e+38, Efficacy_Is_Multiplicative=1,
                 Expired_Event_Trigger=Campaign_Event_Enum.NoTrigger, Intervention_Name=None,
                 New_Property_Value=None, Vaccine_Take=1, Vaccine_Type=Vaccine_Type_Enum.Generic,
                 Waning_Config={}, **kwargs):
        self.Cost_To_Consumer = Cost_To_Consumer
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Distributed_Event_Trigger = Distributed_Event_Trigger          # enum
        self.Dont_Allow_Duplicates = Dont_Allow_Duplicates                  # bool: 0
        self.Duration_To_Wait_Before_Revaccination = Duration_To_Wait_Before_Revaccination
        self.Efficacy_Is_Multiplicative = Efficacy_Is_Multiplicative
        self.Expired_Event_Trigger = Expired_Event_Trigger                  # enum
        self.Intervention_Name = Intervention_Name
        self.New_Property_Value = New_Property_Value
        self.Vaccine_Take = Vaccine_Take
        self.Vaccine_Type = Vaccine_Type                                    # enum
        self.Waning_Config = Waning_Config

        update_attr(self, **kwargs)


class DelayedIntervention(BaseCampaign):
    def __init__(self, Actual_IndividualIntervention_Configs=[], Coverage=1,
                 Delay_Distribution=Delay_Distribution_Enum.NOT_INITIALIZED, Delay_Period=6, Delay_Period_Max=6,
                 Delay_Period_Mean=6, Delay_Period_Min=6, Delay_Period_Scale=16, Delay_Period_Shape=20,
                 Delay_Period_Std_Dev=6, Disqualifying_Properties=None, Dont_Allow_Duplicates=False,
                 Intervention_Name=None, New_Property_Value=None, **kwargs):
        self.Actual_IndividualIntervention_Configs = Actual_IndividualIntervention_Configs
        self.Coverage = Coverage
        self.Delay_Distribution = Delay_Distribution                # enum
        self.Delay_Period = Delay_Period
        self.Delay_Period_Max = Delay_Period_Max
        self.Delay_Period_Mean = Delay_Period_Mean
        self.Delay_Period_Min = Delay_Period_Min
        self.Delay_Period_Scale = Delay_Period_Scale
        self.Delay_Period_Shape = Delay_Period_Shape
        self.Delay_Period_Std_Dev = Delay_Period_Std_Dev
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Dont_Allow_Duplicates = Dont_Allow_Duplicates          # bool: 0
        self.Intervention_Name = Intervention_Name
        self.New_Property_Value = New_Property_Value

        update_attr(self, **kwargs)


class HumanHostSeekingTrap(BaseCampaign):
    def __init__(self, Attract_Config={}, Cost_To_Consumer=3.75, Disqualifying_Properties=None,
                 Dont_Allow_Duplicates=False, Intervention_Name=None, Killing_Config={},
                 New_Property_Value=None, Primary_Decay_Time_Constant=0,
                 Secondary_Decay_Time_Constant=1, **kwargs):
        self.Attract_Config = Attract_Config
        self.Cost_To_Consumer = Cost_To_Consumer
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Dont_Allow_Duplicates = Dont_Allow_Duplicates          # bool: 0
        self.Intervention_Name = Intervention_Name
        self.Killing_Config = Killing_Config
        self.New_Property_Value = New_Property_Value
        self.Primary_Decay_Time_Constant = Primary_Decay_Time_Constant
        self.Secondary_Decay_Time_Constant = Secondary_Decay_Time_Constant

        update_attr(self, **kwargs)


class IndividualImmunityChanger(BaseCampaign):
    def __init__(self, Boost_Acquire=0, Boost_Mortality=0, Boost_Threshold_Acquire=0,
                 Boost_Threshold_Mortality=0, Boost_Threshold_Transmit=0, Boost_Transmit=0,
                 Cost_To_Consumer=10, Prime_Acquire=0, Prime_Mortality=0, Prime_Transmit=0,
                 **kwargs):
        self.Boost_Acquire = Boost_Acquire
        self.Boost_Mortality = Boost_Mortality
        self.Boost_Threshold_Acquire = Boost_Threshold_Acquire
        self.Boost_Threshold_Mortality = Boost_Threshold_Mortality
        self.Boost_Threshold_Transmit = Boost_Threshold_Transmit
        self.Boost_Transmit = Boost_Transmit
        self.Cost_To_Consumer = Cost_To_Consumer
        self.Prime_Acquire = Prime_Acquire
        self.Prime_Mortality = Prime_Mortality
        self.Prime_Transmit = Prime_Transmit

        update_attr(self, **kwargs)


class InsectKillingFenceHousingModification(BaseCampaign):
    def __init__(self, Blocking_Config={}, Cost_To_Consumer=8, Disqualifying_Properties=None,
                 Dont_Allow_Duplicates=False, Intervention_Name=None, Killing_Config={},
                 New_Property_Value=None, Primary_Decay_Time_Constant=0,
                 Secondary_Decay_Time_Constant=1, **kwargs):
        self.Blocking_Config = Blocking_Config
        self.Cost_To_Consumer = Cost_To_Consumer
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Dont_Allow_Duplicates = Dont_Allow_Duplicates          # bool: 0
        self.Intervention_Name = Intervention_Name
        self.Killing_Config = Killing_Config
        self.New_Property_Value = New_Property_Value
        self.Primary_Decay_Time_Constant = Primary_Decay_Time_Constant
        self.Secondary_Decay_Time_Constant = Secondary_Decay_Time_Constant

        update_attr(self, **kwargs)


class IRSHousingModification(BaseCampaign):
    def __init__(self, Blocking_Config={}, Cost_To_Consumer=8, Disqualifying_Properties=None,
                 Dont_Allow_Duplicates=False, Intervention_Name=None, Killing_Config={},
                 New_Property_Value=None, Primary_Decay_Time_Constant=0, Secondary_Decay_Time_Constant=1,
                 **kwargs):
        self.Blocking_Config = Blocking_Config
        self.Cost_To_Consumer = Cost_To_Consumer
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Dont_Allow_Duplicates = Dont_Allow_Duplicates          # bool: 0
        self.Intervention_Name = Intervention_Name
        self.Killing_Config = Killing_Config
        self.New_Property_Value = New_Property_Value
        self.Primary_Decay_Time_Constant = Primary_Decay_Time_Constant
        self.Secondary_Decay_Time_Constant = Secondary_Decay_Time_Constant

        update_attr(self, **kwargs)


class IVCalendar(BaseCampaign):
    def __init__(self, Actual_IndividualIntervention_Configs=[], Age=None, Calendar=[],
                 Disqualifying_Properties=None, Dont_Allow_Duplicates=False, Dropout=False,
                 Intervention_Name=None, New_Property_Value=None, Probability=None,
                 **kwargs):
        self.Actual_IndividualIntervention_Configs = Actual_IndividualIntervention_Configs
        self.Age = Age
        self.Calendar = Calendar
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Dont_Allow_Duplicates = Dont_Allow_Duplicates      # bool: 0
        self.Dropout = Dropout                                  # bool: 0
        self.Intervention_Name = Intervention_Name
        self.New_Property_Value = New_Property_Value
        self.Probability = Probability

        update_attr(self, **kwargs)


class Ivermectin(BaseCampaign):
    def __init__(self, Cost_To_Consumer=8, Disqualifying_Properties=None, Dont_Allow_Duplicates=False,
                 Intervention_Name=None, Killing_Config={}, New_Property_Value=None,
                 **kwargs):
        self.Cost_To_Consumer = Cost_To_Consumer
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Dont_Allow_Duplicates = Dont_Allow_Duplicates          # bool: 0
        self.Intervention_Name = Intervention_Name
        self.Killing_Config = Killing_Config
        self.New_Property_Value = New_Property_Value

        update_attr(self, **kwargs)


class MalariaDiagnostic(BaseCampaign):
    def __init__(self, Base_Sensitivity=1, Base_Specificity=1, Cost_To_Consumer=1, Days_To_Diagnosis=0,
                 Detection_Threshold=100, Diagnostic_Type=Diagnostic_Type_Enum.Microscopy,
                 Disqualifying_Properties=None, Dont_Allow_Duplicates=False,
                 Event_Or_Config=Event_Or_Config_Enum.Config, Intervention_Name=None,
                 New_Property_Value=None, Positive_Diagnosis_Config={},
                 Positive_Diagnosis_Event=Campaign_Event_Enum.NoTrigger, Treatment_Fraction=1,
                 **kwargs):
        self.Base_Sensitivity = Base_Sensitivity
        self.Base_Specificity = Base_Specificity
        self.Cost_To_Consumer = Cost_To_Consumer
        self.Days_To_Diagnosis = Days_To_Diagnosis
        self.Detection_Threshold = Detection_Threshold
        self.Diagnostic_Type = Diagnostic_Type                          # enum
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Dont_Allow_Duplicates = Dont_Allow_Duplicates              # bool: 0
        self.Event_Or_Config = Event_Or_Config                          # enum
        self.Intervention_Name = Intervention_Name
        self.New_Property_Value = New_Property_Value
        self.Positive_Diagnosis_Config = Positive_Diagnosis_Config
        self.Positive_Diagnosis_Event = Positive_Diagnosis_Event        # enum
        self.Treatment_Fraction = Treatment_Fraction

        update_attr(self, **kwargs)


class MigrateIndividuals(BaseCampaign):
    def __init__(self, Disqualifying_Properties=None, Dont_Allow_Duplicates=False,
                 Duration_At_Node_Distribution_Type=Duration_At_Node_Distribution_Type_Enum.NOT_INITIALIZED,
                 Duration_At_Node_Exponential_Period=6, Duration_At_Node_Fixed=6, Duration_At_Node_Gausian_Mean=6,
                 Duration_At_Node_Gausian_StdDev=1, Duration_At_Node_Poisson_Mean=6, Duration_At_Node_Uniform_Max=0,
                 Duration_At_Node_Uniform_Min=0,
                 Duration_Before_Leaving_Distribution_Type=Duration_Before_Leaving_Distribution_Type_Enum.NOT_INITIALIZED,
                 Duration_Before_Leaving_Exponential_Period=6, Duration_Before_Leaving_Fixed=6,
                 Duration_Before_Leaving_Gausian_Mean=6, Duration_Before_Leaving_Gausian_StdDev=1,
                 Duration_Before_Leaving_Poisson_Mean=6, Duration_Before_Leaving_Uniform_Max=0,
                 Duration_Before_Leaving_Uniform_Min=0, Intervention_Name=None, Is_Moving=False,
                 New_Property_Value=None, NodeID_To_Migrate_To=0, **kwargs):
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Dont_Allow_Duplicates = Dont_Allow_Duplicates                              # bool: 0
        self.Duration_At_Node_Distribution_Type = Duration_At_Node_Distribution_Type    # enum
        self.Duration_At_Node_Exponential_Period = Duration_At_Node_Exponential_Period
        self.Duration_At_Node_Fixed = Duration_At_Node_Fixed
        self.Duration_At_Node_Gausian_Mean = Duration_At_Node_Gausian_Mean
        self.Duration_At_Node_Gausian_StdDev = Duration_At_Node_Gausian_StdDev
        self.Duration_At_Node_Poisson_Mean = Duration_At_Node_Poisson_Mean
        self.Duration_At_Node_Uniform_Max = Duration_At_Node_Uniform_Max
        self.Duration_At_Node_Uniform_Min = Duration_At_Node_Uniform_Min
        self.Duration_Before_Leaving_Distribution_Type = Duration_Before_Leaving_Distribution_Type      # enum
        self.Duration_Before_Leaving_Exponential_Period = Duration_Before_Leaving_Exponential_Period
        self.Duration_Before_Leaving_Fixed = Duration_Before_Leaving_Fixed
        self.Duration_Before_Leaving_Gausian_Mean = Duration_Before_Leaving_Gausian_Mean
        self.Duration_Before_Leaving_Gausian_StdDev = Duration_Before_Leaving_Gausian_StdDev
        self.Duration_Before_Leaving_Poisson_Mean = Duration_Before_Leaving_Poisson_Mean
        self.Duration_Before_Leaving_Uniform_Max = Duration_Before_Leaving_Uniform_Max
        self.Duration_Before_Leaving_Uniform_Min = Duration_Before_Leaving_Uniform_Min
        self.Intervention_Name = Intervention_Name
        self.Is_Moving = Is_Moving                          # bool: 0
        self.New_Property_Value = New_Property_Value
        self.NodeID_To_Migrate_To = NodeID_To_Migrate_To

        update_attr(self, **kwargs)


class MultiEffectBoosterVaccine(BaseCampaign):
    def __init__(self, Acquire_Config={}, Boost_Acquire=0, Boost_Mortality=0, Boost_Threshold_Acquire=0,
                 Boost_Threshold_Mortality=0, Boost_Threshold_Transmit=0, Boost_Transmit=0, Cost_To_Consumer=10,
                 Disqualifying_Properties=None, Dont_Allow_Duplicates=False, Intervention_Name=None,
                 Mortality_Config={}, New_Property_Value=None, Prime_Acquire=0, Prime_Mortality=0,
                 Prime_Transmit=0, Transmit_Config={}, Vaccine_Take=1, **kwargs):
        self.Acquire_Config = Acquire_Config
        self.Boost_Acquire = Boost_Acquire
        self.Boost_Mortality = Boost_Mortality
        self.Boost_Threshold_Acquire = Boost_Threshold_Acquire
        self.Boost_Threshold_Mortality = Boost_Threshold_Mortality
        self.Boost_Threshold_Transmit = Boost_Threshold_Transmit
        self.Boost_Transmit = Boost_Transmit
        self.Cost_To_Consumer = Cost_To_Consumer
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Dont_Allow_Duplicates = Dont_Allow_Duplicates          # bool: 0
        self.Intervention_Name = Intervention_Name
        self.Mortality_Config = Mortality_Config
        self.New_Property_Value = New_Property_Value
        self.Prime_Acquire = Prime_Acquire
        self.Prime_Mortality = Prime_Mortality
        self.Prime_Transmit = Prime_Transmit
        self.Transmit_Config = Transmit_Config
        self.Vaccine_Take = Vaccine_Take

        update_attr(self, **kwargs)


class MultiEffectVaccine(BaseCampaign):
    def __init__(self, Acquire_Config={}, Cost_To_Consumer=10, Disqualifying_Properties=None,
                 Dont_Allow_Duplicates=False, Intervention_Name=None, Mortality_Config={},
                 New_Property_Value=None, Transmit_Config={}, Vaccine_Take=1, **kwargs):
        self.Acquire_Config = Acquire_Config
        self.Cost_To_Consumer = Cost_To_Consumer
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Dont_Allow_Duplicates = Dont_Allow_Duplicates          # bool: 0
        self.Intervention_Name = Intervention_Name
        self.Mortality_Config = Mortality_Config
        self.New_Property_Value = New_Property_Value
        self.Transmit_Config = Transmit_Config
        self.Vaccine_Take = Vaccine_Take

        update_attr(self, **kwargs)


class MultiInterventionDistributor(BaseCampaign):
    def __init__(self,Disqualifying_Properties=None, Dont_Allow_Duplicates=False, Intervention_List=[],
                 Intervention_Name=None, New_Property_Value=None, Number_Repetitions=1,
                 Timesteps_Between_Repetitions=-1,  **kwargs):
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Dont_Allow_Duplicates = Dont_Allow_Duplicates      # bool: 0
        self.Intervention_List = Intervention_List
        self.Intervention_Name = Intervention_Name
        self.New_Property_Value = New_Property_Value
        self.Number_Repetitions = Number_Repetitions
        self.Timesteps_Between_Repetitions = Timesteps_Between_Repetitions

        update_attr(self, **kwargs)


class OutbreakIndividual(BaseCampaign):
    def __init__(self, Antigen=0, Genome=0, Ignore_Immunity=True, Incubation_Period_Override=-1, **kwargs):
        self.Antigen = Antigen
        self.Genome = Genome
        self.Ignore_Immunity = Ignore_Immunity          # bool: 1
        self.Incubation_Period_Override = Incubation_Period_Override

        update_attr(self, **kwargs)


class PropertyValueChanger(BaseCampaign):
    def __init__(self, Daily_Probability=1, Disqualifying_Properties=None, Dont_Allow_Duplicates=False,
                 Intervention_Name=None, Maximum_Duration=3.4e+38, New_Property_Value=None, Revert=0,
                 Target_Property_Key=None, Target_Property_Value=None, **kwargs):
        self.Daily_Probability = Daily_Probability
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Dont_Allow_Duplicates = Dont_Allow_Duplicates           # bool: 0
        self.Intervention_Name = Intervention_Name
        self.Maximum_Duration = Maximum_Duration
        self.New_Property_Value = New_Property_Value
        self.Revert = Revert
        self.Target_Property_Key = Target_Property_Key
        self.Target_Property_Value = Target_Property_Value

        update_attr(self, **kwargs)


class RTSSVaccine(BaseCampaign):
    def __init__(self, Antibody_Type=Antibody_Type_Enum.CSP, Antibody_Variant=0,
                 Boosted_Antibody_Concentration=1, Cost_To_Consumer=3.75, Disqualifying_Properties=None,
                 Dont_Allow_Duplicates=False, Intervention_Name=None, New_Property_Value=None, **kwargs):
        self.Antibody_Type = Antibody_Type                          # enum
        self.Antibody_Variant = Antibody_Variant
        self.Boosted_Antibody_Concentration = Boosted_Antibody_Concentration
        self.Cost_To_Consumer = Cost_To_Consumer
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Dont_Allow_Duplicates = Dont_Allow_Duplicates          # bool: 0
        self.Intervention_Name = Intervention_Name
        self.New_Property_Value = New_Property_Value

        update_attr(self, **kwargs)


class ScreeningHousingModification(BaseCampaign):
    def __init__(self, Blocking_Config={}, Cost_To_Consumer=8, Disqualifying_Properties=None,
                 Dont_Allow_Duplicates=False, Intervention_Name=None, Killing_Config={},
                 New_Property_Value=None, Primary_Decay_Time_Constant=0,
                 Secondary_Decay_Time_Constant=1, **kwargs):
        self.Blocking_Config = Blocking_Config
        self.Cost_To_Consumer = Cost_To_Consumer
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Dont_Allow_Duplicates = Dont_Allow_Duplicates          # bool: 0
        self.Intervention_Name = Intervention_Name
        self.Killing_Config = Killing_Config
        self.New_Property_Value = New_Property_Value
        self.Primary_Decay_Time_Constant = Primary_Decay_Time_Constant
        self.Secondary_Decay_Time_Constant = Secondary_Decay_Time_Constant

        update_attr(self, **kwargs)


class SimpleBednet(BaseCampaign):
    def __init__(self, Blocking_Config={}, Cost_To_Consumer=3.75, Disqualifying_Properties=None,
                 Dont_Allow_Duplicates=False, Intervention_Name=None, Killing_Config={},
                 New_Property_Value=None, Primary_Decay_Time_Constant=0, Secondary_Decay_Time_Constant=1,
                 Usage_Config={}, Bednet_Type=None, **kwargs):
        self.Blocking_Config = Blocking_Config
        self.Cost_To_Consumer = Cost_To_Consumer
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Dont_Allow_Duplicates = Dont_Allow_Duplicates              # bool: 0
        self.Intervention_Name = Intervention_Name
        self.Killing_Config = Killing_Config
        self.New_Property_Value = New_Property_Value
        self.Primary_Decay_Time_Constant = Primary_Decay_Time_Constant
        self.Secondary_Decay_Time_Constant = Secondary_Decay_Time_Constant
        self.Usage_Config = Usage_Config
        self.Bednet_Type = Bednet_Type                                  # is missing, NOT USED

        update_attr(self, **kwargs)


class SimpleBoosterVaccine(BaseCampaign):
    def __init__(self, Boost_Effect=1, Boost_Threshold=0, Cost_To_Consumer=10, Disqualifying_Properties=None,
                 Dont_Allow_Duplicates=False, Efficacy_Is_Multiplicative=True, Intervention_Name=None,
                 New_Property_Value=None, Prime_Effect=1, Vaccine_Take=1,
                 Vaccine_Type=Vaccine_Type_Enum.Generic, Waning_Config={}, **kwargs):
        self.Boost_Effect = Boost_Effect
        self.Boost_Threshold = Boost_Threshold
        self.Cost_To_Consumer = Cost_To_Consumer
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Dont_Allow_Duplicates = Dont_Allow_Duplicates              # bool: 0
        self.Efficacy_Is_Multiplicative = Efficacy_Is_Multiplicative    # bool: 1
        self.Intervention_Name = Intervention_Name
        self.New_Property_Value = New_Property_Value
        self.Prime_Effect = Prime_Effect
        self.Vaccine_Take = Vaccine_Take
        self.Vaccine_Type = Vaccine_Type                                # enum
        self.Waning_Config = Waning_Config

        update_attr(self, **kwargs)


class SimpleDiagnostic(BaseCampaign):
    def __init__(self, Cost_To_Consumer=1, Days_To_Diagnosis=0, Disqualifying_Properties=None,
                 Dont_Allow_Duplicates=False, Intervention_Name=None, New_Property_Value=None,
                 Positive_Diagnosis_Config={}, Positive_Diagnosis_Event=Campaign_Event_Enum.NoTrigger,
                 Treatment_Fraction=1, **kwargs):
        self.Cost_To_Consumer = Cost_To_Consumer
        self.Days_To_Diagnosis = Days_To_Diagnosis
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Dont_Allow_Duplicates = Dont_Allow_Duplicates               # bool: 0
        self.Intervention_Name = Intervention_Name
        self.New_Property_Value = New_Property_Value
        self.Positive_Diagnosis_Config = Positive_Diagnosis_Config
        self.Positive_Diagnosis_Event = Positive_Diagnosis_Event         # enum
        self.Treatment_Fraction = Treatment_Fraction

        update_attr(self, **kwargs)


class SimpleHealthSeekingBehavior(BaseCampaign):
    def __init__(self, Actual_IndividualIntervention_Config={},
                 Actual_IndividualIntervention_Event=Campaign_Event_Enum.NoTrigger,
                 Disqualifying_Properties=None, Dont_Allow_Duplicates=False,
                 Event_Or_Config=Event_Or_Config_Enum.Config, Intervention_Name=None,
                 New_Property_Value=None, Single_Use=True, Tendency=1, **kwargs):
        self.Actual_IndividualIntervention_Config = Actual_IndividualIntervention_Config
        self.Actual_IndividualIntervention_Event = Actual_IndividualIntervention_Event      # enum
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Dont_Allow_Duplicates = Dont_Allow_Duplicates              # bool: 0
        self.Event_Or_Config = Event_Or_Config                          # enum
        self.Intervention_Name = Intervention_Name
        self.New_Property_Value = New_Property_Value
        self.Single_Use = Single_Use                                    # bool: 1
        self.Tendency = Tendency

        update_attr(self, **kwargs)


class SimpleHousingModification(BaseCampaign):
    def __init__(self, Blocking_Config={}, Cost_To_Consumer=8, Disqualifying_Properties=None,
                 Dont_Allow_Duplicates=False, Intervention_Name=None, Killing_Config={},
                 New_Property_Value=None, **kwargs):
        self.Blocking_Config = Blocking_Config
        self.Cost_To_Consumer = Cost_To_Consumer
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Dont_Allow_Duplicates = Dont_Allow_Duplicates          # bool: 0
        self.Intervention_Name = Intervention_Name
        self.Killing_Config = Killing_Config
        self.New_Property_Value = New_Property_Value

        update_attr(self, **kwargs)


class SimpleIndividualRepellent(BaseCampaign):
    def __init__(self, Blocking_Config={}, Cost_To_Consumer=8, Disqualifying_Properties=None,
                 Dont_Allow_Duplicates=False, Intervention_Name=None, New_Property_Value=None,
                 Primary_Decay_Time_Constant=0, Secondary_Decay_Time_Constant=1, **kwargs):
        self.Blocking_Config = Blocking_Config
        self.Cost_To_Consumer = Cost_To_Consumer
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Dont_Allow_Duplicates = Dont_Allow_Duplicates               # bool: 0
        self.Intervention_Name = Intervention_Name
        self.New_Property_Value = New_Property_Value
        self.Primary_Decay_Time_Constant = Primary_Decay_Time_Constant
        self.Secondary_Decay_Time_Constant = Secondary_Decay_Time_Constant

        update_attr(self, **kwargs)


class SimpleVaccine(BaseCampaign):
    def __init__(self, Cost_To_Consumer=10, Disqualifying_Properties=None, Dont_Allow_Duplicates=False,
                 Efficacy_Is_Multiplicative=True, Event_Or_Config=Event_Or_Config_Enum.Config,
                 Intervention_Name=None, New_Property_Value=None, Vaccine_Take=1,
                 Vaccine_Type=Vaccine_Type_Enum.Generic, Waning_Config={}, **kwargs):
        self.Cost_To_Consumer = Cost_To_Consumer
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Dont_Allow_Duplicates = Dont_Allow_Duplicates              # bool: 0
        self.Efficacy_Is_Multiplicative = Efficacy_Is_Multiplicative    # bool: 1
        self.Event_Or_Config = Event_Or_Config                          # enum
        self.Intervention_Name = Intervention_Name
        self.New_Property_Value = New_Property_Value
        self.Vaccine_Take = Vaccine_Take
        self.Vaccine_Type = Vaccine_Type                                # enum
        self.Waning_Config = Waning_Config

        update_attr(self, **kwargs)


class SpatialRepellentHousingModification(BaseCampaign):
    def __init__(self, Blocking_Config={}, Cost_To_Consumer=8, Disqualifying_Properties=None,
                 Dont_Allow_Duplicates=False, Intervention_Name=None, Killing_Config={},
                 New_Property_Value=None, Primary_Decay_Time_Constant=0,
                 Secondary_Decay_Time_Constant=1, **kwargs):
        self.Blocking_Config = Blocking_Config
        self.Cost_To_Consumer = Cost_To_Consumer
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Dont_Allow_Duplicates = Dont_Allow_Duplicates          # bool: 0
        self.Intervention_Name = Intervention_Name
        self.Killing_Config = Killing_Config
        self.New_Property_Value = New_Property_Value
        self.Primary_Decay_Time_Constant = Primary_Decay_Time_Constant
        self.Secondary_Decay_Time_Constant = Secondary_Decay_Time_Constant

        update_attr(self, **kwargs)


class UsageDependentBednet(BaseCampaign):
    def __init__(self, Blocking_Config={}, Cost_To_Consumer=3.75, Discard_Event=Campaign_Event_Enum.NoTrigger,
                 Disqualifying_Properties=None, Dont_Allow_Duplicates=False,
                 Expiration_Distribution_Type=Expiration_Distribution_Type_Enum.NOT_INITIALIZED,
                 Expiration_Percentage_Period_1=0.5, Expiration_Period=6.0, Expiration_Period_1=6,
                 Expiration_Period_2=6, Expiration_Period_Max=0, Expiration_Period_Mean=6,
                 Expiration_Period_Min=0, Expiration_Period_Std_Dev=1, Intervention_Name=None,
                 Killing_Config={}, New_Property_Value=None, Received_Event=Campaign_Event_Enum.NoTrigger,
                 Usage_Config_List=None, Using_Event=Campaign_Event_Enum.NoTrigger, **kwargs):
        self.Blocking_Config = Blocking_Config
        self.Cost_To_Consumer = Cost_To_Consumer
        self.Discard_Event = Discard_Event                                      # enum
        self.Disqualifying_Properties = Disqualifying_Properties
        self.Dont_Allow_Duplicates = Dont_Allow_Duplicates                      # bool: 0
        self.Expiration_Distribution_Type = Expiration_Distribution_Type        # enum
        self.Expiration_Percentage_Period_1 = Expiration_Percentage_Period_1
        self.Expiration_Period = Expiration_Period
        self.Expiration_Period_1 = Expiration_Period_1
        self.Expiration_Period_2 = Expiration_Period_2
        self.Expiration_Period_Max = Expiration_Period_Max
        self.Expiration_Period_Mean = Expiration_Period_Mean
        self.Expiration_Period_Min = Expiration_Period_Min
        self.Expiration_Period_Std_Dev = Expiration_Period_Std_Dev
        self.Intervention_Name = Intervention_Name
        self.Killing_Config = Killing_Config
        self.New_Property_Value = New_Property_Value
        self.Received_Event = Received_Event                                    # enum
        self.Usage_Config_List = Usage_Config_List
        self.Using_Event = Using_Event                                          # enum

        update_attr(self, **kwargs)






###################################
# Missing classes
###################################

class NodeSetNodeList(BaseCampaign):
    def __init__(self, Node_List=[], **kwargs):
        self.Node_List = Node_List

        update_attr(self, **kwargs)


class IncidenceEventCoordinator(BaseCampaign):
    def __init__(self, Incidence_Counter=None, Number_Repetitions=1000,
                 Responder=None, Timesteps_Between_Repetitions=30.0, **kwargs):
        self.Incidence_Counter = Incidence_Counter
        self.Number_Repetitions = Number_Repetitions
        self.Responder = Responder
        self.Timesteps_Between_Repetitions = Timesteps_Between_Repetitions

        update_attr(self, **kwargs)


class NodeSetAll(BaseCampaign):
    def __init__(self, **kwargs):

        update_attr(self, **kwargs)



###################################
# Our classes
###################################

class Campaign(BaseCampaign):
    def __init__(self, Campaign_Name='Empty Campaign', Use_Defaults=1, Events=[], **kwargs):
        self.Campaign_Name = Campaign_Name
        self.Use_Defaults = Use_Defaults
        self.Events = Events

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
    an = aClass()
    attrs = vars(an)
    return attrs


def build_argument(cls)  :
    # print(list_all_attr(cls))
    attr_dict = list_all_attr(cls)
    attr_list = ['%s=%s' % (k, v) for k, v in attr_dict.items()]
    prop_list = ['self.%s = %s\n' % (k, k) for k, v in attr_dict.items()]
    print(', '.join(attr_list))
    print()
    print(''.join(prop_list))


if __name__ == "__main__":
    # list_all_attr(Campaign)

    build_argument(NodeLevelHealthTriggeredIV)

    pass