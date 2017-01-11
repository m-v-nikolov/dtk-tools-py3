import platform

def get_os():
    """
    Retrieve OS
    """

    sy = platform.system()

    # OS: windows
    if sy == 'Windows':
        my_os = 'win'
    # OS: Linux
    elif sy == 'Linux':
        my_os = 'lin'
    # OS: Mac
    else:
        my_os = 'mac'

    return my_os