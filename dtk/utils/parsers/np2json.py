import json
import numpy as np


class NumpyAwareJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray) and obj.ndim == 1:
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


# convert a 1D numpy array to valid json     
def np2json(arr, output="data.json"):
    with open(output, 'w+') as f:
        if arr.ndim == 1:
            json.dump(arr, f, cls=NumpyAwareJSONEncoder)
        elif arr.ndim == 2:  # ugly... very ugly; need to extend the decoder
            f.write("[")
            for i, r in enumerate(arr):
                json.dump(r, f, cls=NumpyAwareJSONEncoder)
                if i + 1 < len(arr):
                    f.write(",")
            f.write("]")
        else:
            print("Unsupported array dimension " + str(arr.ndim) + ". Max. supported dimension 2")
