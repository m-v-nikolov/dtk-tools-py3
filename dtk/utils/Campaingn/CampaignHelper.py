import json
import sys
from dtk.utils.Campaingn.CampaignEnum import *


class CampaignEncoder(json.JSONEncoder):

    def convert_enum(self, val):
        """
        Map: True/False to 1/0
        """
        return 1 if val else 0

    def default(self, o):
        """
        Specially handle cases:
          - Enum
          - bool
          - Campaign class
        """
        # handle enum case
        if isinstance(o, Enum):
            return o.name

        # First get the dict
        d = o.__dict__

        # handle bool case
        d = {key: self.convert_enum(val) if isinstance(val, bool) else val for key, val in d.items()}

        # Add class
        # for Campaign class we defined, don't output class
        if o.__class__.__name__ != 'Campaign':
            d["class"] = o.__class__.__name__

        return d

    def load_class(self, class_name):
        _class = getattr(sys.modules['dtk.utils.Campaingn.CampaignClass'], class_name)
        return _class


def list_all_attr(aClass):
    attrs = vars(aClass)
    return attrs


def update_attr(cls, **kwargs):

    for k, v in kwargs.items():
        validate_attr(cls, k, v)

        setattr(cls, k, v)


def validate_attr(cls, k, v):
    attr_dict = list_all_attr(cls)
    if k not in attr_dict:
        output_default(cls, k)
        exit()


def output_default(cls, not_param=None):
    if not_param:
        print("'%s' is not a member of class '%s" % (not_param, cls.__class__.__name__))
        print("Available Members of class '%s': " % cls.__class__.__name__)

    _class = getattr(sys.modules['dtk.utils.Campaingn.CampaignClass'], cls.__class__.__name__)
    c = _class()
    c_dict = c.__dict__
    attr_list = ['- %s (default value: %s)' % (k, v) for k, v in c_dict.items()]
    print('\n'.join(attr_list))


class BaseCampaign(object):
    def __init__(self):
        pass

    def to_json(self):
        return json.dumps(self, cls=CampaignEncoder, indent=3)

