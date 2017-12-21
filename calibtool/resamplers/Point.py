import numpy as np
import pandas as pd

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

    def to_dataframe(self):
        df = None
        for p in self.parameters:
            d = p.to_dict()
            d = {k: [v] for k, v in d.items()}
            # print(p.to_dict())
            # print(d)
            if df is None:
                df = pd.DataFrame(d)
            else:
                df = pd.concat([df, pd.DataFrame(d)])
        return df

    def get_settings(self):
        settings = {}
        for p in self.parameters:
            settings[p.name] = {'max': p.max, 'min': p.min, 'guess': p.guess}

        return settings


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

    def to_dataframe(self):
        # pname_list = []
        # center_list = []
        # max_list = []
        # min_list = []
        # for p in input['parameters']:
        #     pname_list.append(p['Name'])
        #     center_list.append(p['Value'])
        #     max_list.append(p['Max'])
        #     min_list.append(p['Min'])
        #
        # df = pd.DataFrame(data={'Name': pname_list, 'Center': center_list, 'Max': max_list, 'Min': min_list})
        # df['Center'] = df['Center'].astype('float')
        # df['Min'] = df['Min'].astype('float')
        # df['Max'] = df['Max'].astype('float')
        # print(df)

        df = pd.DataFrame(self.to_dict())
        return df
