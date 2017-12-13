class Point(object):
    """
    A simple class that acts similarly to a dict, but uses attributes for access
    """
    def __init__(self, items):
        for k,v in items.items():
            setattr(self, k, v)
        self.items = items.keys()

    def to_dict(self):
        result = {}
        for k in self.items:
            result[k] = getattr(self, k)
