import json
import decimal
import numpy as np

class NumpyAwareJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray) and obj.ndim == 1:
            #return [x for x in obj]
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return (float(o) for o in [o])
        return super(DecimalEncoder, self).default(o)