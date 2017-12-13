import os
import pandas as pd

from calibtool.Point import Point

class CalibrationPoints(object):
    def __init__(self, points):
        self.points = points

    def write(self, filename):
        point_dicts = [p.to_dict() for p in self.points]
        point_dataframe = pd.DataFrame(point_dicts)
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        point_dataframe.to_csv(filename, index=False)

    @classmethod
    def read(cls, filename):
        points_as_dicts = pd.DataFrame.from_csv(filename).to_dict(orient='index').values()
        point_list = [Point(p) for p in points_as_dicts.items()]
        return cls(points=point_list)
