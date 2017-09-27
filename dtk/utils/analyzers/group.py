
def no_grouping(simid, metadata):
    return simid


class group_by_name:
    def __init__(self, name):
        self.name = name

    def __call__(self, simid, metadata):
        return metadata.get(self.name, simid)

def group_all(simid, metadata):
    return 'all'


class combo_group:
    def __init__(self,*args):
        self.args = args

    def __call__(self, simid, metadata):
        return tuple(group(simid, metadata) for group in self.args)

def default_group_fn(k,v):
    return k