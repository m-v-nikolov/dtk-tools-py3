def example_filter(sim_metadata):
    rn=sim_metadata.get('Run_Number',None)
    if rn is None:
        print("'Run_Number' key not found in sim_metadata; simulation passing filter.")
        return True
    return (rn > 0)