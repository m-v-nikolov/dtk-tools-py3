class Point:
    """
    A simple class that acts similarly to a dict, but uses attributes for access
    """
    def __init__(self, items):
        self.__dict__ = items
        self.items = items.keys()

    def to_dict(self):
        result = {}
        for k in self.items:
            result[k] = getattr(self, k)
