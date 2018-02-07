from dtk.interventions.triggered_campaign_delay_event import triggered_campaign_delay_event
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.utils.Campaingn.CampaignClass import *
from dtk.utils.Campaingn.CampaignHelper import CampaignEncoder
from dtk.utils.Campaingn.CampaignEnum import list_all_enums


def load_json_data(filename):
    try:
        return json.load(open(filename, 'rb'))
    except IOError:
        raise Exception('Unable to read file: %s' % 'campaign.json')


def list_modules_classes():
    import sys
    import inspect

    cm = campaign_modules = sys.modules['dtk.utils.Campaingn.CampaignClass']
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


def get_all_enums():
    list_all_enums()


def get_all_classes():
    list_all_classes()


def test_modules():
    import sys
    import inspect

    cm = campaign_modules = sys.modules['dtk.utils.Campaingn.CampaignClass']
    print('Type: ', type(cm))
    # print('length: ', len(cm))
    print(cm)

    print(help(cm))
    print('------------')
    print(dir(cm))
    print('------------')
    print(cm.__dict__)

    print('--- List all classes ---')
    clsmembers = inspect.getmembers(cm, inspect.isclass)
    print('Type: ', type(clsmembers))
    print('Length: ', len(clsmembers))
    print(clsmembers)


def list_members_of_class(aClass):
    members = all_members(aClass)

    print(members)


def all_members(aClass):
    """
    https://www.safaribooksonline.com/library/view/python-cookbook/0596001673/ch05s03.html
    :param aClass:
    :return:
    """
    try:
        # Try getting all relevant classes in method-resolution order
        mro = list(aClass.__mro__)
    except AttributeError:
        # If a class has no _ _mro_ _, then it's a classic class
        def getmro(aClass, recurse):
            mro = [aClass]
            for base in aClass.__bases__:
                mro.extend(recurse(base, recurse))

            return mro
        mro = getmro(aClass, getmro)

    mro.reverse()
    members = {}
    for someClass in mro:
        members.update(vars(someClass))

    return members


def list_methods(aClass):
    """
    Note: seems not workikng
    :param aClass:
    :return:
    """

    import inspect

    variables = [i for i in dir(aClass) if inspect.ismethod(i)]
    # t = aClass()
    # variables = [i for i in dir(t) if inspect.ismethod(i)]
    # print(variables)

    # an = aClass()
    # attrs = [attr for attr in dir(an) if not attr.startswith('__')]
    # print(attrs)

    # list all attributes
    an = aClass()
    attrs = vars(an)
    print(attrs)


def test_object():
    a = InputEIR()
    # a = InputEIR(Intervention_Name=5)
    # a = InsectKillingFence(Intervention_Name=5)
    print(a.to_json())


def create_SimpleBednet():
    b = SimpleBednet(Cost_To_Consumer=10, Dont_Allow_Duplicates=1, New_Property_Value=6, test=9)

    print(b.to_json())


def create_betnet():
    """
        itn_bednet = { "class": "SimpleBednet",
                       "Bednet_Type": "ITN",
                       "Killing_Config": {
                            "Initial_Effect": 0.6,
                            "Decay_Time_Constant": 1460,
                            "class": "WaningEffectExponential"
                        },
                       "Blocking_Config": {
                            "Initial_Effect": 0.9,
                            "Decay_Time_Constant": 730,
                            "class": "WaningEffectExponential"
                        },
                       "Usage_Config": {
                           "Expected_Discard_Time": 3650, # default: keep nets for 10 years
                           "Initial_Effect": 1.0,
                           "class": "WaningEffectRandomBox"
                       },
                       "Cost_To_Consumer": 3.75
        }
    :return:
    """
    receiving_itn_event = BroadcastEvent(Broadcast_Event='Received_ITN')

    itn_bednet = SimpleBednet(Bednet_Type='ITN',
                              Killing_Config=WaningEffectExponential(Initial_Effect=0.6, Decay_Time_Constant=1460),
                              Blocking_Config=WaningEffectExponential(Initial_Effect=0.9, Decay_Time_Constant=730),
                              Usage_Config=WaningEffectRandomBox(Expected_Discard_Time=3650, Initial_Effect=1.0),
                              Cost_To_Consumer=3.75
                              )

    itn_bednet_w_event = MultiInterventionDistributor(Intervention_List=[itn_bednet, receiving_itn_event])

    print(itn_bednet_w_event.to_json())


def test_add_ITN():
    # cb = {}
    cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')
    coverage_by_age = {'min': 0, 'max': 200, 'coverage': 1}
    ITN_event = add_ITN(cb, start=0, coverage_by_ages=[coverage_by_age], waning={}, nodeIDs=[])

    print(ITN_event)
    print(ITN_event.to_json())

def add_ITN(config_builder, start, coverage_by_ages, waning={}, cost=0, nodeIDs=[], node_property_restrictions=[],
            ind_property_restrictions=[], triggered_campaign_delay=0, trigger_condition_list=[], listening_duration=-1):
    """
    Add an ITN intervention to the config_builder passed.
    birth-triggered(in coverage_by_age) and triggered_condition_list are mututally exclusive. "birth" option will be ingnored if you're
    using trigger_condition_list

    :param config_builder: The :py:class:`DTKConfigBuilder <dtk.utils.core.DTKConfigBuilder>` holding the campaign that will receive the ITN event
    :param start: The start day of the bednet distribution
    :param coverage_by_ages: a list of dictionaries defining the coverage per age group
        [{"coverage":1,"min": 1, "max": 10},{"coverage":1,"min": 11, "max": 50},{ "coverage":0.5, "birth":"birth", "duration":34}]
    :param waning: a dictionary defining the durability of the nets. if empty the default decay profile will be used.
    For example, update usage duration to 180 days as waning={'Usage_Config' : {"Expected_Discard_Time": 180}}
    :param cost: Set the ``Cost_To_Consumer`` parameter
    :param nodeIDs: If empty, all nodes will get the intervention. If set, only the nodeIDs specified will receive the intervention.
    :param node_property_restrictions: restricts itn based on list of node properties in format [{"Place":"RURAL"}, {"ByALake":"Yes, "LovelyWeather":"No}]
    :param ind_property_restrictions: Restricts itn based on list of individual properties in format [{"BitingRisk":"High", "IsCool":"Yes}, {"IsRich": "Yes"}]
    :param triggered_campaign_delay: how many time steps after receiving the trigger will the campaign start.
    Eligibility of people or nodes for campaign is evaluated on the start day, not the triggered day.
    :param trigger_condition_list: when not empty,  the start day is the day to start listening for the trigger conditions listed, distributing the spraying
        when the trigger is heard. This does not distribute the BirthTriggered intervention.
    :param listening_duration: how long the distributed event will listen for the trigger for, default is -1, which is indefinitely
    :return: Nothing
    """

    receiving_itn_event = BroadcastEvent(Broadcast_Event='Received_ITN')

    itn_bednet = SimpleBednet(Bednet_Type='ITN',
                              Killing_Config=WaningEffectExponential(Initial_Effect=0.6, Decay_Time_Constant=1460),
                              Blocking_Config=WaningEffectExponential(Initial_Effect=0.9, Decay_Time_Constant=730),
                              Usage_Config=WaningEffectRandomBox(Expected_Discard_Time=3650, Initial_Effect=1.0),
                              Cost_To_Consumer=3.75
                              )

    # [TODO]
    # if waning:
    #     for cfg in waning :
    #         itn_bednet[cfg].update(waning[cfg])

    itn_bednet.Cost_To_Consumer = cost

    itn_bednet_w_event = MultiInterventionDistributor(Intervention_List=[itn_bednet, receiving_itn_event])

    # Assign node IDs #
    # Defaults to all nodes unless a node set is specified
    if not nodeIDs:
        nodeset_config = NodeSetAll()
    else:
        nodeset_config = NodeSetNodeList(Node_List=nodeIDs)

    if triggered_campaign_delay:
        trigger_condition_list = [str(triggered_campaign_delay_event(config_builder, start,  nodeIDs,
                                                                   triggered_campaign_delay, trigger_condition_list,
                                                                                             listening_duration))]

    for coverage_by_age in coverage_by_ages:
        if trigger_condition_list:
            if not 'birth' in coverage_by_age.keys():
                intervention_config = NodeLevelHealthTriggeredIV(
                    Trigger_Condition_List=trigger_condition_list,
                    Duration=listening_duration,
                    Demographic_Coverage=coverage_by_age["coverage"],
                    Target_Residents_Only=1,
                    Actual_IndividualIntervention_Config=itn_bednet_w_event  # itn_bednet
                )

                ITN_event = CampaignEvent(Start_Day=int(start),
                                          Nodeset_Config=nodeset_config,
                                          Event_Coordinator_Config=StandardInterventionDistributionEventCoordinator(Intervention_Config=intervention_config)
                                          )

                if all([k in coverage_by_age.keys() for k in ['min', 'max']]):
                    ITN_event_e_i = ITN_event.Event_Coordinator_Config.Intervention_Config
                    ITN_event_e_i.Target_Demographic = "ExplicitAgeRanges"
                    ITN_event_e_i.Target_Age_Min = coverage_by_age["min"]
                    ITN_event_e_i.Target_Age_Max = coverage_by_age["max"]

                if ind_property_restrictions:
                    ITN_event_e_i.Property_Restrictions_Within_Node = ind_property_restrictions

                if node_property_restrictions:
                    ITN_event_e_i.Node_Property_Restrictions = node_property_restrictions

        else:
            event_coordinator_config = StandardInterventionDistributionEventCoordinator(
                Node_Property_Restrictions=[],
                Target_Residents_Only=1,
                Demographic_Coverage=coverage_by_age["coverage"],
                Intervention_Config=itn_bednet_w_event              # itn_bednet
            )
            ITN_event = CampaignEvent(Start_Day=int(start),
                                      Nodeset_Config=nodeset_config,
                                      Event_Coordinator_Config=event_coordinator_config
                                      )

            if node_property_restrictions:
                ITN_event.Event_Coordinator_Config.Node_Property_Restrictions.extend(node_property_restrictions)

            if all([k in coverage_by_age.keys() for k in ['min', 'max']]):
                ITN_event.Event_Coordinator_Config.Target_Demographic = "ExplicitAgeRanges"
                ITN_event.Event_Coordinator_Config.Target_Age_Min = coverage_by_age["min"]
                ITN_event.Event_Coordinator_Config.Target_Age_Max = coverage_by_age["max"]

            if 'birth' in coverage_by_age.keys() and coverage_by_age['birth']:
                birth_triggered_intervention = BirthTriggeredIV(
                    Duration=coverage_by_age.get('duration', -1),               # default to forever if  duration not specified
                    Demographic_Coverage=coverage_by_age["coverage"],
                    Actual_IndividualIntervention_Config=itn_bednet_w_event     # itn_bednet
                )

                ITN_event.Event_Coordinator_Config.Intervention_Config = birth_triggered_intervention
                ITN_event.Event_Coordinator_Config.pop("Demographic_Coverage")      # [TODO]: delete member?
                ITN_event.Event_Coordinator_Config.pop("Target_Residents_Only")     # [TODO]: delete member?

                if ind_property_restrictions:
                    ITN_event.Event_Coordinator_Config.Intervention_Config.Property_Restrictions_Within_Node = ind_property_restrictions

            elif ind_property_restrictions:
                ITN_event.Event_Coordinator_Config.Property_Restrictions_Within_Node = ind_property_restrictions

        config_builder.add_event(ITN_event.to_json())

        # TEST
        return ITN_event


def test1(campaign_data):
    keys = list(campaign_data.keys())
    print(keys)

    events = campaign_data['Events']
    print(type(events))
    print('Events Counts: %s' % len(events))

    print('------ events[0] ------')
    event = events[0]
    print(type(event))
    print(event)
    print(list(event.keys()))


def test2():
    # ce = CampaignEvent()
    # print(ce.event_coordinator_config)
    # print(ce.event_coordinator_config.test)
    # print(json.dumps(ce, cls=CustomEncoder, indent=3))
    # exit()

    d = {
        "Decay_Time_Constant": 270,
        "Initial_Effect": 0.022795411936278643
    }
    w = WaningEffectExponential(**d)
    # w = WaningEffectExponential()
    print(json.dumps(w, cls=CampaignEncoder, indent=3))
    exit()

    # mi = MultiInterventionDistributor()
    # print(json.dumps(mi, cls=CustomEncoder, indent=3))
    # exit()

    sidec = StandardInterventionDistributionEventCoordinator()
    # print(sidec)
    # print(sidec.intervention_config)
    # print(sidec.node_property_restrictions)


    print(json.dumps(sidec, cls=CampaignEncoder, indent=3))
    exit()

    c = Campaign()
    c.add_campaign_event()
    c.add_campaign_event()
    # print(json.dumps(c, cls=CustomEncoder, indent=3))
    print(c.to_json())


def test_enum_output():
    w = WaningEffectMapPiecewise(Expire_At_Durability_Map_End=True)
    print(w.to_json())

    m = MosquitoRelease()
    print(m.to_json())


def test_explicit_arguments():
    # c = CampaignEvent(Start_Day=2, Test=1)
    # c = CalendarEventCoordinator(Target_Age_Min=5, Test=3)
    # c = CommunityHealthWorkerEventCoordinator(Amount_In_Shipment=5, Test=2)
    c = CoverageByNodeEventCoordinator(Demographic_Coverage=5, Test=3)
    print(c.to_json())


if __name__ == "__main__":
    # campaign_file = r'H:\temp\campaign.json'
    # campaign_data = load_json_data(campaign_file)
    #
    # test1(campaign_data)

    # test2()

    # print(sys.modules)

    # test_modules()
    # list_modules_classes()

    # get_all_enums()
    # get_all_classes()

    # list_members_of_class(Campaign)
    # list_methods(Campaign)

    # test_enum()
    # test_enum_output()

    # test_object()
    # create_SimpleBednet()
    # create_betnet()

    test_add_ITN()

    # test_explicit_arguments()

    pass


