def example_filter(sim_metadata):
    rn=sim_metadata.get('Run_Number',None)
    if rn is None:
        print("'Run_Number' key not found in sim_metadata; simulation passing filter.")
        return True
    return (rn > 0)

def name_match_filter(substr):
    def f(sim_metadata):
        Config_Name=sim_metadata.get('Config_Name',None)
        if Config_Name is None:
            print("'Config_Name' key not found in sim_metadata; simulation passing filter.")
            return Config_Name
        return (substr in Config_Name)
    return f