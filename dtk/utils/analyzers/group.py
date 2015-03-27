def no_grouping(simid,metadata):
    return simid

def group_by_name(name):
    def fn(simid,metadata):
        return metadata.get(name,simid)
    return fn

def group_all(simid,metadata):
    return 'all'