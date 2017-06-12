def example_filter(metadata):
    rn = metadata.get('Run_Number', None)
    if rn is None:
        print("'Run_Number' key not found in metadata; simulation passing filter.")
        return True
    return rn > 0


def name_match_filter(substr):

    def f(metadata):
        config_name = metadata.get('Config_Name', None)
        if config_name is None:
            print("'Config_Name' key not found in metadata; simulation passing filter.")
            return config_name
        return substr in config_name

    return f


def key_value_within(key, value, threshold):

    def f(metadata):
        sim_value = metadata[key]
        return abs(sim_value - value) < threshold

    return f


def key_value_equals(key, value):
    return lambda metadata: metadata[key] == value


def key_value_isin(key, values):
    return lambda metadata: metadata[key] in values


def combo_filter(*args):
    def f(metadata):
        return all(filter(metadata) for filter in args)

    return f


def default_filter_fn(md):
    return True
