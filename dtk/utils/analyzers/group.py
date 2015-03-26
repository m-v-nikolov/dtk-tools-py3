def no_grouping(simid,metadata):
    return simid

def group_by_name(simid,metadata):
    return metadata.get('Config_Name',simid)

def group_all(simid,metadata):
    return 'all'