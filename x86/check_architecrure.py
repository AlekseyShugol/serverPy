import platform

def check_system_bitness():
    bitness = platform.architecture()[0]
    return bitness
