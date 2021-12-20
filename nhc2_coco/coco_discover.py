import binascii
import select
import threading
import socket
import netifaces
from getmac import get_mac_address
import logging


_LOGGING = logging.getLogger(__name__)

class CoCoDiscover:
    """CoCoDiscover will help you discover NHC2.
    It will also tell you about NHC1, but the result will differ.

    You create CoCoDiscover, passing along a callback an the time you max want to wait.
    By default we wait 3 seconds.

    For every result with matching header the callback is called,
    with the address, mac-address and a boolean if it's a NHC2.
    """

    def __init__(self, on_discover, on_done):
        self._on_discover = on_discover
        self._on_done = on_done
        # If we discover one, we don't want to keep looking too long...
        self._discovered_at_least_one = False
        self._thread = threading.Thread(target=self._scan_for_nhc)
        self._thread.start()
        _LOGGING.info(f"CoCoDiscover started with callbacks: {on_discover}, {on_done}")


    @staticmethod
    def _get_broadcast_ips():
        notNone = lambda x: x
        if2bcast = lambda i: netifaces.ifaddresses(i).get(netifaces.AF_INET, [{}])[0].get('broadcast')
        return set(filter(notNone, map(if2bcast, netifaces.interfaces())))

    def _scan_for_nhc(self):
        _LOGGING.debug("start scanning nhc")
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # We search for all broadcast ip4s, so that we don't only search the main interface
        broadcast_ips = CoCoDiscover._get_broadcast_ips()
        _LOGGING.info(f'Available broadcast IPS to check = {broadcast_ips}')
        for broadcast_ip in broadcast_ips:
            server.sendto(bytes([0x44]), (broadcast_ip, 10000))
            _LOGGING.info(f"broadcast 0x44 sent to {broadcast_ip}")
        server.setblocking(0)
        loops = 0

        # min 20 max 200 tries to discover at least one
        while loops < 200 and ((not self._discovered_at_least_one) or loops < 20):
            loops += 1
            ready = select.select([server], [], [], 0.01)
            if ready[0]:
                data, addr = server.recvfrom(4096)
                if data[0] == 0x44:  # NHC2 Header
                    is_nhc2 = (len(data) >= 16) and (data[15] == 0x02)
                    mac = get_mac_address(ip=addr[0])
                    _LOGGING.info(f"discovery at ip({addr[0]}) - mac({mac}) - is_nhc2({is_nhc2})")
                    if self._on_discover:
                        self._discovered_at_least_one = True
                        self._on_discover(addr[0], mac, is_nhc2)
                        _LOGGING.debug(f"discovery callback done")
        server.close()
        self._on_done()
        _LOGGING.debug("done scanning nhc")
