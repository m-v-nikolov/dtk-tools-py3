import base64
import datetime
import json
import numpy as np


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        """If input object is an ndarray it will be converted into a dict 
        holding dtype, shape and the data, base64 encoded.
        """
        if isinstance(obj, np.int64):
            return int(obj)  # because JSON doesn't know what to do with np.int64 (on Windows)
        elif isinstance(obj, np.ndarray):
            if obj.flags['C_CONTIGUOUS']:
                obj_data = obj.data
            else:
                cont_obj = np.ascontiguousarray(obj)
                assert(cont_obj.flags['C_CONTIGUOUS'])
                obj_data = cont_obj.data
            data_b64 = base64.b64encode(obj_data).decode('utf-8')
            return dict(__ndarray__=data_b64,
                        dtype=str(obj.dtype),
                        shape=obj.shape)
        try:
            # Let the base class default method raise the TypeError
            return super(NumpyEncoder, self).default(obj)
        except TypeError:
            return str(obj)


class GeneralEncoder(NumpyEncoder):
    def default(self, obj):
        from COMPS.Data.Simulation import SimulationState
        from simtools.DataAccess.Schema import Simulation

        if isinstance(obj, SimulationState):
            return obj.name
        elif isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, datetime.datetime):
            return str(obj)
        elif isinstance(obj, Simulation):
            return obj.toJSON()
        return super(GeneralEncoder, self).default(obj)


def json_numpy_obj_hook(dct):
    """Decodes a previously encoded numpy ndarray with proper shape and dtype.

    :param dct: (dict) json encoded ndarray
    :return: (ndarray) if input was an encoded ndarray
    """
    if isinstance(dct, dict) and '__ndarray__' in dct:
        data = base64.b64decode(dct['__ndarray__'])
        return np.frombuffer(data, dct['dtype']).reshape(dct['shape'])
    return dct


def cast_number(val):
    """
    Try casting the value to float/int returns str if cannot
    :param val: the value to cast
    :return: value casted
    """
    if "." in str(val):
        try:
            return float(val)
        except (ValueError, TypeError):
            return val
    try:
        return int(val)
    except (ValueError, TypeError):
        return val

