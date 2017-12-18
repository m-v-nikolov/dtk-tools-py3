class CalibrationPoint:
    def __init__(self, parameters=None, likelihood=None):
        self.parameters = parameters
        self.likelihood = likelihood

    def to_value_dict(self):
        """
        Return the dict of dict containing {parameter_name:value} for this CalibrationPoint
        """
        return {param.name: param.value for param in self.parameters}

    def to_dict(self):
        return {"parameters": [param.to_dict() for param in self.parameters],
                "likelihood": self.likelihood}


class CalibrationParameter:
    def __init__(self, name, min, max, value=None, mapTo=None, dynamic=True, guess=None):
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
                   min=parameters["Min"], max=parameters["Max"],
                   guess=parameters.get("Guess", None),
                   mapTo=parameters.get("MapTo", None),
                   dynamic=parameters.get("Dynamic", True),
                   value=parameters.get("Value", None))

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
