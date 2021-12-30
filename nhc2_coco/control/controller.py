""" Main controller class builds a local python representation of the nhc2 Controller
It also acts as a proxy to interact with the system
"""
from .mqtt import Nhc2Messenger, Nhc2Connection


class Nhc2Controller:

    def __init__(self, connection Nhc2Connection):
        self._mqtt = Nhc2MQMessenger(connection)
        self._mqtt.start()

    @property
    def devices(self):
        pass

    def find_device(self, qry):
        pass
