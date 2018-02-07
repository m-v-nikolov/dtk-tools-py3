from enum import Enum

##################################
# Events and event coordinators
##################################

class Target_Demographic_Enum(Enum):
    Everyone = 0
    ExplicitAgeRanges = 1
    ExplicitAgeRangesAndGender = 2
    ExplicitGender = 3
    PossibleMothers = 4
    ArrivingAirTravellers = 5
    DepartingAirTravellers = 6
    ArrivingRoadTravellers = 7
    DepartingRoadTravellers = 8
    AllArrivingTravellers = 9
    AllDepartingTravellers = 10
    ExplicitDiseaseState = 11


class Target_Gender_Enum(Enum):
    Male = 0
    Female = 1
    All = 2


class Initial_Amount_Distribution_Type_Enum(Enum):
    NOT_INITIALIZED = 0
    FIXED_DURATION = 1
    UNIFORM_DURATION = 2
    GAUSSIAN_DURATION = 3
    EXPONENTIAL_DURATION = 4
    POISSON_DURATION = 5
    LOG_NORMAL_DURATION = 6
    BIMODAL_DURATION = 7
    PIECEWISE_CONSTANT = 8
    PIECEWISE_LINEAR = 9
    WEIBULL_DURATION = 10
    DUAL_TIMESCALE_DURATION = 11


class Target_Demographic_Enum(Enum):
    Everyone = 0
    ExplicitAgeRanges = 1
    ExplicitAgeRangesAndGender = 2
    ExplicitGender = 3
    PossibleMothers = 4
    ArrivingAirTravellers = 5
    DepartingAirTravellers = 6
    ArrivingRoadTravellers = 7
    DepartingRoadTravellers = 8
    AllArrivingTravellers = 9
    AllDepartingTravellers = 10
    ExplicitDiseaseState = 11



#########################################
# Node-level interventions
#########################################

class Artificial_Diet_Target_Enum(Enum):
    AD_WithinVillage = 0
    AD_OutsideVillage = 1

class Age_Dependence_Enum(Enum):
    OFF = 0
    LINEAR = 1
    SURFACE_AREA_DEPENDENT = 2

class Habitat_Target_Enum(Enum):
    TEMPORARY_RAINFALL = 0
    WATER_VEGETATION = 1
    HUMAN_POPULATION = 2
    CONSTANT = 3
    BRACKISH_SWAMP = 3
    MARSHY_STREAM = 5
    LINEAR_SPLINE = 6
    ALL_HABITATS = 7

class Challenge_Type_Enum(Enum):
    InfectiousBites = 0
    Sporozoites = 1

class Duration_At_Node_Distribution_Type_Enum(Enum):
    NOT_INITIALIZED = 0
    FIXED_DURATION = 1
    UNIFORM_DURATION = 2
    GAUSSIAN_DURATION = 3
    EXPONENTIAL_DURATION = 4
    POISSON_DURATION = 5
    LOG_NORMAL_DURATION = 6
    BIMODAL_DURATION = 7
    PIECEWISE_CONSTANT = 8
    PIECEWISE_LINEAR = 9
    WEIBULL_DURATION = 10
    DUAL_TIMESCALE_DURATION = 11


class Duration_Before_Leaving_Distribution_Type_Enum(Enum):
    NOT_INITIALIZED = 0
    FIXED_DURATION = 1
    UNIFORM_DURATION = 2
    GAUSSIAN_DURATION = 3
    EXPONENTIAL_DURATION = 4
    POISSON_DURATION = 5
    LOG_NORMAL_DURATION = 6
    BIMODAL_DURATION = 7
    PIECEWISE_CONSTANT = 8
    PIECEWISE_LINEAR = 9
    WEIBULL_DURATION = 10
    DUAL_TIMESCALE_DURATION = 11


class Pesticide_Resistance_Enum(Enum):
    WILD = 0
    HALF = 1
    FULL = 2
    NotMated = 3


class Released_Gender_Enum(Enum):
    VECTOR_FEMALE = 0
    VECTOR_MALE = 1


class Released_Sterility_Enum(Enum):
    VECTOR_FERTILE = 0
    VECTOR_STERILE = 1


class Released_Wolbachia_Enum(Enum):
    WOLBACHIA_FREE = 0
    VECTOR_WOLBACHIA_A = 1
    VECTOR_WOLBACHIA_B = 2
    VECTOR_WOLBACHIA_AB = 3


class Blackout_Event_Trigger_Enum(Enum):
    """
    Will use general Campaign_Event_Enum
    Here definition will be used as an indicator: member Blackout_Event_Trigger is an enum
    """
    pass


class Trigger_Condition_List_Enum(Enum):
    """
    Will use general Campaign_Event_Enum
    Here definition will be used as an indicator: member Trigger_Condition_List is an enum
    """
    pass



class Demographic_Coverage_Time_Profile_Enum(Enum):
    Immediate = 0
    Linear = 1
    Sigmoid = 2


class Spray_Kill_Target_Enum(Enum):
    SpaceSpray_FemalesOnly = 0
    SpaceSpray_MalesOnly = 1
    SpaceSpray_FemalesAndMales = 2
    SpaceSpray_Indoor = 3



#######################################
# Individual-level interventions
#######################################

class Dosing_Type_Enum(Enum):
    FullTreatmentCourse = 0
    FullTreatmentParasiteDetect = 1
    FullTreatmentNewDetectionTech = 2
    FullTreatmentWhenSymptom = 3
    Prophylaxis = 4
    SingleDose = 5
    SingleDoseNewDetectionTech = 6
    SingleDoseParasiteDetect = 7
    SingleDoseWhenSymptom = 8


class Drug_Type_Enum(Enum):
    Artemether_Lumefantrine = 0
    Artemisinin = 1
    Chloroquine = 2
    GenPreerythrocytic = 3
    GenTransBlocking = 4
    Primaquine = 5
    Quinine = 6
    SP = 7
    Tafenoquine = 8


class Event_Trigger_Enum(Enum):
    """
    Will use general Campaign_Event_Enum
    Here definition will be used as an indicator: member Event_Trigger is an enum
    """
    pass


class BroadcastEvent_Enum(Enum):
    """
    Will use general Campaign_Event_Enum
    Here definition will be used as an indicator: member BroadcastEvent is an enum
    """
    pass


class Node_Selection_Type_Enum(Enum):
    DISTANCE_ONLY = 0
    MIGRATION_NODES_ONLY = 1
    DISTANCE_AND_MIGRATION = 2


class Distributed_Event_Trigger_Enum(Enum):
    """
    Will use general Campaign_Event_Enum
    Here definition will be used as an indicator: member Distributed_Event_Trigger is an enum
    """
    pass


class Expired_Event_Trigger_Enum(Enum):
    """
    Will use general Campaign_Event_Enum
    Here definition will be used as an indicator: member Expired_Event_Trigger is an enum
    """
    pass


class Vaccine_Type_Enum(Enum):
    Generic = 0
    TransmissionBlocking = 1
    AcquisitionBlocking = 2
    MortalityBlocking = 3


class Delay_Distribution_Enum(Enum):
    NOT_INITIALIZED = 0
    FIXED_DURATION = 1
    UNIFORM_DURATION = 2
    GAUSSIAN_DURATION = 3
    EXPONENTIAL_DURATION = 4
    POISSON_DURATION = 5
    LOG_NORMAL_DURATION = 6
    BIMODAL_DURATION = 7
    PIECEWISE_CONSTANT = 8
    PIECEWISE_LINEAR = 9
    WEIBULL_DURATION = 10
    DUAL_TIMESCALE_DURATION = 11


class Diagnostic_Type_Enum(Enum):
    Microscopy = 0
    NewDetectionTech = 1
    Other = 2


class Event_Or_Config_Enum(Enum):
    Event = 0
    Config = 1


class Positive_Diagnosis_Event_Enum(Enum):
    """
    Will use general Campaign_Event_Enum
    Here definition will be used as an indicator: member Positive_Diagnosis_Event is an enum
    """
    pass


class Antibody_Type_Enum(Enum):
    CSP = 0
    MSP1 = 1
    PfEMP1_minor = 2
    PfEMP1_major = 3
    N_MALARIA_ANTIBODY_TYPES = 4


class Actual_IndividualIntervention_Event_Enum(Enum):
    """
    Will use general Campaign_Event_Enum
    Here definition will be used as an indicator: member Actual_IndividualIntervention_Event is an enum
    """
    pass


class Discard_Event_Enum(Enum):
    """
    Will use general Campaign_Event_Enum
    Here definition will be used as an indicator: member Discard_Event is an enum
    """
    pass


class Expiration_Distribution_Type_Enum(Enum):
    NOT_INITIALIZED = 0
    FIXED_DURATION = 1
    UNIFORM_DURATION = 2
    GAUSSIAN_DURATION = 3
    EXPONENTIAL_DURATION = 4
    POISSON_DURATION = 5
    LOG_NORMAL_DURATION = 6
    BIMODAL_DURATION = 7
    PIECEWISE_CONSTANT = 8
    PIECEWISE_LINEAR = 9
    WEIBULL_DURATION = 10
    DUAL_TIMESCALE_DURATION = 11


class Received_Event_Enum(Enum):
    """
    Will use general Campaign_Event_Enum
    Here definition will be used as an indicator: member Received_Event is an enum
    """
    pass


class Using_Event_Enum(Enum):
    """
    Will use general Campaign_Event_Enum
    Here definition will be used as an indicator: member Using_Event is an enum
    """
    pass




#####################################
# Waning effect classes
# None
#####################################


#####################################
# Event Enum Mapping
# Note: all map to Campaign_Event_Enum
#####################################
EVENT_MAPPING = ['Blackout_Event_Trigger_Enum', 'Trigger_Condition_List_Enum', 'Event_Trigger_Enum',
                 'Distributed_Event_Trigger_Enum', 'Expired_Event_Trigger_Enum', 'Positive_Diagnosis_Event_Enum',
                 'Actual_IndividualIntervention_Event_Enum', 'Discard_Event_Enum', 'Received_Event_Enum', 'Using_Event_Enum']


#####################################
# Event List
# Will be used for some enum members
#####################################

class Campaign_Event_Enum(Enum):
    Births = 0
    DiseaseDeaths = 1
    EighteenMonthsOld = 2
    Emigrating = 3
    EnteredRelationship = 4
    EveryTimeStep = 5
    EveryUpdate = 6
    ExitedRelationship = 7
    FirstCoitalAct = 8
    FourteenWeeksPregnant = 9
    GaveBirth = 10
    HappyBirthday = 11
    HIVNewlyDiagnosed = 12
    HIVNonPreARTToART = 13
    HIVPreARTToART = 14
    HIVSymptomatic = 15
    HIVTestedNegative = 16
    HIVTestedPositive = 17
    Immigrating = 18
    InterventionDisqualified = 19
    NewClinicalCase = 20
    NewInfectionEvent = 21
    NewSevereCase = 22
    NodePropertyChange = 23
    NonDiseaseDeaths = 24
    NoTrigger = 25
    Pregnant = 26
    PropertyChange = 27
    ProviderOrdersTBTest = 28
    SixWeeksOld = 29
    StartedART = 30
    STIDebut = 31
    STINewInfection = 32
    STIPostImmigrating = 33
    STIPreEmigrating = 34
    StoppedART = 35
    TBActivation = 36
    TBActivationExtrapulm = 37
    TBActivationPostRelapse = 38
    TBActivationPresymptomatic = 39
    TBActivationSmearNeg = 40
    TBActivationSmearPos = 41
    TBFailedDrugRegimen = 42
    TBMDRTestDefault = 43
    TBMDRTestNegative = 44
    TBMDRTestPositive = 45
    TBPendingRelapse = 46
    TBRelapseAfterDrugRegimen = 47
    TBRestartHSB = 48
    TBStartDrugRegimen = 48
    TBStopDrugRegimen = 50
    TBTestDefault = 51
    TBTestNegative = 52
    TBTestPositive = 53
    TestPositiveOnSmear = 54
    TwelveWeeksPregnant = 55








def list_all_enums():
    import sys
    import inspect

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
    clsmembers = inspect.getmembers(cm, inspect.isclass)
    print('Type: ', type(clsmembers))
    print('Length: ', len(clsmembers))
    print(clsmembers)



if __name__ == "__main__":
    list_all_enums()
    pass





