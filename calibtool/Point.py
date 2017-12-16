from copy import deepcopy

class Point:
    """
    A simple class that acts similarly to a dict, but uses attributes for access on its Params
    e.g. point.Value, not some_dict['Value']
    """
    def __init__(self, params_dict, likelihood=None):
        self._params = {}
        for name, data in params_dict.items():
            self._params[name] = Param(data)
        self._items = self._params.keys()
        self.likelihood = likelihood # no value by default

    def list_params(self):
        return self._params.keys()

    def get_param(self, name):
        return self._params.get(name, None)

    def set_param_value(self, name, value):
        # ck4, I think this is right. Needs a quick test to verify the override takes hold and is visible after .to_dict(), too.
        self.get_param(name).Value = value

    def to_dict(self, only_key=None):
        """
        Return the dict of dict representation of this Point object
        :param only_key: if not None, then return a dict of {param_name:only_key_value, ...}
        :return: a dict of dicts; top level keys are parameter names. Second level keys are parameter metadata items
        """
        result = {}
        if only_key:
            # we will collapse the result to a single dict of param_name:value(only_key)
            # Useful for building simulations
            for param_name in self._items:
                result[param_name] = getattr(self.get_param(param_name), only_key)
        else:
            for param_name in self._items:
                result[param_name] = self.get_param(param_name).to_dict()
        return result

    # ck4, this method is untested, though in principle it is pretty simple :)
    @classmethod
    def copy(cls, point):
        """
        Returns a copy of the provided Point object
        :param point: a Point object
        :return:
        """
        return cls(point.to_dict(), likelihood=point.likelihood)

class Param:
    def __init__(self, items):
        self.__dict__ = deepcopy(items) # without this, the self.items list contains itself ('items')
        self.items = items.keys()

    def to_dict(self):
        result = {}
        for k in self.items:
            result[k] = getattr(self, k)
        return result
