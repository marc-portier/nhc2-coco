import asyncio
import os
import logging
import paho.mqtt.client as mqtt
from nhc2_coco.const import MQTT_PROTOCOL, MQTT_TRANSPORT

loop = asyncio.get_event_loop()
_LOGGER=logging.getLogger(__name__)

class CoCoLoginValidation:
    """ Validate one can login on the CoCo
    """
    def __init__(self, address, username, password, port=8883, ca_path=None):
        self._address = address
        self._username = username
        self._password = password
        self._port = port
        self._ca_path = ca_path
        if self._ca_path is None:
            self._ca_path = os.path.dirname(os.path.realpath(__file__)) + '/coco_ca.pem'


    async def check_connection(self, timeout=10):
        # refactoring::suggestion allow this class to do this message translataion too, either return tuple, or have some staticmethod response_as_text
        """ Try to connect with given parameters
            The return indicates success or not:
                0: Connection successful
                1: Connection refused - incorrect protocol version
                2: Connection refused - invalid client identifier
                3: Connection refused - server unavailable
                4: Connection refused - bad username or password
                5: Connection refused - not authorised
                6-255: Currently unused.
        """
        result_code = 0
        done_testing = asyncio.Event()
        client = self._generate_client()

        def done():
            nonlocal done_testing
            done_testing.set()

        def on_connect(x, xx, xxx, reason_code):
            nonlocal result_code
            result_code = reason_code
            loop.call_soon_threadsafe(callback=done)

        client.on_connect = on_connect
        client.loop_start()
        client.connect_async(self._address, self._port, keepalive=timeout)

        try:
            await asyncio.wait_for(done_testing.wait(), timeout + 2)
        except asyncio.TimeoutError:
            pass  # perfectly normal if this occurs
        except Exception as e:
            # refactoring::addition - rather log it then simply ignore
            _LOGGER.excpetion(e)

        client.disconnect()
        client.loop_stop()
        return result_code

    def _generate_client(self):
        client = mqtt.Client(protocol=MQTT_PROTOCOL, transport=MQTT_TRANSPORT)
        client.username_pw_set(self._username, self._password)
        client.tls_set(self._ca_path)
        client.tls_insecure_set(True)
        return client
