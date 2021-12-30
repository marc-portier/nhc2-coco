""" Class hierarchy describing the entities under control of the nhc2
"""
from enum import Enum
from typing import NamedTuple
from abc import abstractmethod


class Nhc2PropertyType():
    @abstractmethod
    def validate(value):
        pass


class Nhc2RangePropertyType(Nhc2PropertyType, NamedTuple):
    min: int
    max: int
    step: int


class Nhc2BooleanPropertyType(Nhc2PropertyType):
    pass


class Nhc2TextPropertyType(Nhc2PropertyType):
    pass


class Nhc2ChoicePropertyType(Nhc2PropertyType, NamedTuple):
    choices: list


class Nhc2DevicePropertyDefinition(NamedTuple):
    """ Structure of a Device Property
    """
    # Name of the property
    name: str
    # Indicates the type of variable.
    type: Nhc2PropertyType
    """ Text field with following options:
    - Range (Minimum value, Maximum value, Stepsize)
    - Boolean (True, False)
    - Text (text field)
    - Choice (List of discrete values)
    """
    # Indicates whether the property has status information and is capable to report it
    status: bool
    # Indicates whether the property can be controlled via the control command
    control: bool
    # Indicates whether the property can be used in a weekly schedule program
    schedule: bool
    """ Remark: schedules cannot be accessed or configured via the hobby API
    """
    # Indicates whether the property reports measurement information (15 minute granularity)
    logging: bool
    """ Remark: this measurement data is not accessible via the hobby API
    """


class Nhc2DeviceProperties(dict):
    pass


class Nhc2DeviceDescriptor(NamedTuple):
    """ Describing all devices (which includes players and actions)
    """
    # Unique Identifier within the Niko Home Control Platform,
    # used for addressing the device in e.g. the location list and control device commands
    uuid: str
    # Device application type
    type: str
    # Defines the manufacturer of the device
    technology: str
    # Defines the hardware model
    model: str
    # Niko Home Control configuration identifier
    identifier: str
    # Human readable, display name of the device, can be updated by the user installer
    name: str
    # List of device specific context features
    traits: list  # probably can be a dict !
    """ Device traits are device specific details (which are fixed) providing more context about the device.
    - available traits depend on the DeviceClass
    - they seem to have just a name and a value
    """
    # List of device configuration options  -- depends on DeviceClass
    parameters: list  # probably can be a dict !
    """ Device parameters are typically fields that are filled in during configuration and commissioning
    of the installation. The values of those fields do not change during normal operational use of the
    installation.
    Note that there are devices having the same device class and using different content.
    - available parameters depend on the DeviceClass
    - they seem to have just a name and a value
    """
    # List of run-time functions
    properties: Nhc2DeviceProperties
    """ Device properties can be considered as run-time functionality of a device. The values of those
    properties are changing regularly during normal operation use of the system.
    - available properties depend on the DeviceClass
    - they have a structure modelled through Nhc2DeviceProperty
    """
