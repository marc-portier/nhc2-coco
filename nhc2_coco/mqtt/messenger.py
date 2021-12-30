""" Handles the actual MQTT messaging towards the nhc2 Controller
"""


from enum import Enum
from typing import NamedTuple
import os




def lead_dots_trail(s, lead=2, dots=2, trail=3):
    """ shortened variant of s: int-lead chars from the start, followed by int-dots dots, completed with int-trail chars from the end
    """
    return f"{s[:lead]}{'.' * dots}{s[(-1 * trail):]}"


class Nhc2Connection(NamedTuple):
    host: str
    password: str
    port: int = 8884
    ca_path: str = Nhc2Connection.default_ca_path()

    CERTFILE_NAME = "niko-ca.pem"

    @staticmethod
    def default_ca_path():
        """ returns path to default certificate-authority-file
        """
        return os.join(os.path.dirname(os.path.realpath(__file__)), Nhc2Connection.CERTFILE_NAME)

    def as_tuple(self):
        """ elements of this class as a tuple one can explode
        """
        return tuple(self)

    @property
    def secret(self):
        """ hidden variant of the password - enough to recognise, not enough to become an issue by carelessly sharing in logs
        """
        return lead_dots_trail(self.password)

    def __repr__(self):
        return f"{type(self).__name__}({self.host}, {self.password}, {self.port}, {self.ca_path})"

    def __str__(self):
        return f"Connection to (host={self.host}, port={self.port}) using password '{self.secret}'"
