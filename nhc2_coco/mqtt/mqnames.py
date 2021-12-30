from enum import Enum
from typing import NamedTuple
from abc import abstractmethod


class Nhc2MQTopicPart(Enum):     # BaseClass for the parts of the topic channels used in the nhc2 mqtt
    """ BaseClass for the various parts making up the MQTT topics in use by nhc2
    """
    @property
    def part(self):
        """ The «part»/«part»/«part»/«part» section of the topic
        """
        return self.value


class Nhc2MQConnector(Nhc2MQTopicPart):
    """ 1st part of the nhcs-mqtt-topic describes the so called 'connector'
    """
    HOBBY = 'hobby'                # Isolated and secure communication channel for a specific user or device profile


class Nhc2MQService(Nhc2MQTopicPart):
    """ 2nd part of the nhcs-mqtt-topic describes the so called 'api-service'
    """
    CONTROL = 'control'            # Control service: to connect and control the Niko Home Control platform
    SYSTEM = 'system'              # System service: system related information
    NOTIFICATION = 'notification'  # Notification service: notification message related information


class Nhc2MQMessageClass(Nhc2MQTopicPart):  # Application domain: defines the context of the message
    """ 3rd part of the nhcs-mqtt-topic describes the so called 'message-class'
    """
    DEVICES = 'devices'
    LOCATIONS = 'locations'


class MQTTMethod(Enum):
    """ The possible methods to apply to a MQTT Topic
    """
    PUBLISH = 'publish'
    SUBSCRIBE = 'subscribe'


class Nhc2MQMessageType(Nhc2MQTopicPart):
    """ 4th part of the nhcs-mqtt-topic describes the so called 'message-type'
    """
    # Command messages
    CMD = ('cmd', MQTTMethod.PUBLISH)
    # Event messages
    EVT = ('evt', MQTTMethod.SUBSCRIBE)
    # Response message as reaction upon a command, having an explicit reply.
    RSP = ('rsp', MQTTMethod.SUBSCRIBE)
    # error message
    ERR = ('err', MQTTMethod.SUBSCRIBE)

    @property
    def part(self):
        return self.value[0]

    @property
    def method(self):
        """ the allowed MQTTMethod for this type of nhc2_mqtt_messages
        """
        return self.value[1]


class Nhc2MQTopic(NamedTuple):
    """ Represents a topic to publish/subscribe to which simply consists of the 4 ordered parts of the path
    """
    connector: Nhc2MQConnector
    service: Nhc2MQService
    message_class: Nhc2MQMessageClass
    message_type: Nhc2MQMessageType

    def __repr__(self):
        return f"{type(self).__name__}({self.connector})"

    @property
    def parts(self):
        return tuple(filter(lambda x:x, tuple(self)))

    @property
    def path(self):
        return '/'.join(p.part for p in self.parts)

    @property
    def method(self):
        return self.message_type.method

    def __str__(self):
        return f"MQTT «topic» {self.path}"
