from enum import Enum


class CoCoDeviceClass(Enum):
    # refactoring::addition this allows to iterate the enum instances
    __order__ = 'SWITCHES LIGHTS SHUTTERS FANS SWITCHED_FANS THERMOSTATS GENERIC'
    SWITCHES = 'switches'
    LIGHTS = 'lights'
    SHUTTERS = 'shutters'
    FANS = 'fans'
    SWITCHED_FANS = 'switched-fans'
    THERMOSTATS = 'thermostats'
    GENERIC = 'generic'
