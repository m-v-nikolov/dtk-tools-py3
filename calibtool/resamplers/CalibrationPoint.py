import json
import pandas as pd
import numpy as np

class CalibrationPoint:
    DYNAMIC = 'dynamic'
    STATIC = 'static'
    ALL = 'all'
    PARAMETER_TYPES = [DYNAMIC, STATIC, ALL]

    LIST = 'list'
    SERIES = 'series'
    NUMPY = 'numpy'

    def __init__(self, parameters=None, likelihood=None):
        self.parameters = parameters
        self.likelihood = likelihood
        self.dimensionality = len(self.parameters)


    def _filter_parameters(self, parameter_type=None):
        """
        Returns a list of parameters that are dynamic, static, or both, sorted by name.
        :param parameter_type: cls.ALL, DYNAMIC, or STATIC
        :return: a list of CalibrationParameter objects
        """
        parameter_type = parameter_type or self.ALL
        if parameter_type not in self.PARAMETER_TYPES:
            raise Exception('parameter_type must be one of: %s' % self.PARAMETER_TYPES)

        keep_dynamic = parameter_type in [self.ALL, self.DYNAMIC]
        keep_static = parameter_type in [self.ALL, self.STATIC]
        filtered_parameters = [p for p in self.parameters if (keep_dynamic and p.dynamic) or (keep_static and not p.dynamic)]
        filtered_parameters = sorted(filtered_parameters, key=lambda p: p.name)
        return filtered_parameters


    def to_value_dict(self, parameter_type=None):
        """
        Return the dict of dict containing {parameter_name:value} for this CalibrationPoint
        """
        return {param.name: param.value for param in self._filter_parameters(parameter_type)}


    def get_attribute(self, key, parameter_type=None, as_type=None):
        """
        Returns the specified attribute of each CalibrationParameter as a list, ordered by parameter
        name.
        :param key:
        :return:
        """
        considered_params = self._filter_parameters(parameter_type=parameter_type)
        attrs = [getattr(param, key.lower()) for param in considered_params]
        as_type = as_type or self.LIST
        if as_type == self.SERIES:
            attrs = pd.Series(attrs)
        elif as_type == self.NUMPY:
            attrs = np.array(attrs)
        return attrs


    @property
    def parameter_names(self, parameter_type=None):
        return self.get_attribute('Name', parameter_type=parameter_type)


    def get_parameter(self, name):
        """
        Relies on their being exactly one parameter with the given name.
        :param name:
        :return:
        """
        return [param for param in self.parameters if param.name == name][0]


    def to_dict(self):
        return {"parameters": [param.to_dict() for param in self.parameters],
                "likelihood": self.likelihood}


    def to_dataframe(self, parameter_type=None):
        df = None
        for p in self._filter_parameters(parameter_type):
            d = p.to_dict()
            d = {k: [v] for k, v in d.items()}
            if df is None:
                df = pd.DataFrame(d)
            else:
                df = pd.concat([df, pd.DataFrame(d)])
        return df


    def write_point(self, filename):
        with open(filename, 'w') as f:
            json.dump(self.to_dict(), f)


class CalibrationParameter:
    def __init__(self, name, min, max, value, mapTo, dynamic, guess):
        self.name = name
        self.min = min
        self.max = max
        self.value = value
        self.mapTo = mapTo
        self.dynamic = dynamic
        self.guess = guess

    @classmethod
    def from_dict(cls, parameters):
        return cls(name=parameters["Name"],
                   min=parameters["Min"],
                   max=parameters["Max"],
                   guess=parameters['Guess'],
                   mapTo=parameters['MapTo'],
                   dynamic=parameters['Dynamic'],
                   value=parameters['Value'])

    @classmethod
    def from_calibration_parameter(cls, parameter, value):
        """
        Create a new CalibrationParameter object from another one but with a new value.
        :param parameter: input CalibrationParameter to copy
        :param value: the value to override the copy with
        :return: a CalibrationParameter object
        """
        new_parameter = cls.from_dict(parameter.to_dict())
        new_parameter.value = value
        return new_parameter


    def to_dict(self):
        return {
            "Name": self.name,
            "Min": self.min,
            "Max": self.max,
            "MapTo": self.mapTo,
            "Guess": self.guess,
            "Value": self.value,
            "Dynamic": self.dynamic
        }

    def to_dataframe(self):
        df = pd.DataFrame(self.to_dict())
        return df
