import json
import logging
import os
import threading
from time import sleep
from typing import Callable

import paho.mqtt.client as mqtt

from .coco_device_class import CoCoDeviceClass
from .coco_fan import CoCoFan
from .coco_light import CoCoLight
from .coco_shutter import CoCoShutter
from .coco_switch import CoCoSwitch
from .coco_switched_fan import CoCoSwitchedFan
from .coco_climate import CoCoThermostat
from .coco_generic import CoCoGeneric

from .const import *
from .helpers import *

_LOGGER = logging.getLogger(__name__)

# refactoring::warning one semaphore globally - in contrast to separate threads per CoCo instance ?
sem = threading.Semaphore()
DEVICE_SETS = {
    CoCoDeviceClass.SWITCHED_FANS: {INTERNAL_KEY_CLASS: CoCoSwitchedFan, INTERNAL_KEY_MODELS: LIST_VALID_SWITCHED_FANS},
    CoCoDeviceClass.FANS: {INTERNAL_KEY_CLASS: CoCoFan, INTERNAL_KEY_MODELS: LIST_VALID_FANS},
    CoCoDeviceClass.SHUTTERS: {INTERNAL_KEY_CLASS: CoCoShutter, INTERNAL_KEY_MODELS: LIST_VALID_SHUTTERS},
    CoCoDeviceClass.SWITCHES: {INTERNAL_KEY_CLASS: CoCoSwitch, INTERNAL_KEY_MODELS: LIST_VALID_SWITCHES},
    CoCoDeviceClass.LIGHTS: {INTERNAL_KEY_CLASS: CoCoLight, INTERNAL_KEY_MODELS: LIST_VALID_LIGHTS},
    CoCoDeviceClass.THERMOSTATS: {INTERNAL_KEY_CLASS: CoCoThermostat, INTERNAL_KEY_MODELS: LIST_VALID_THERMOSTATS},
    CoCoDeviceClass.GENERIC: {INTERNAL_KEY_CLASS: CoCoGeneric, INTERNAL_KEY_MODELS: LIST_VALID_GENERICS}
}


class CoCo:
    def __init__(self, address, username, password, port=8883, ca_path=None, switches_as_lights=False):

        _LOGGER.info(f"initializing Coco({address}, {username}, {password[:3]}...{password[-2:]}, {port}")
        # refactoring::warning -- local instance variable with an effect on a global variable !!! (considered harmfull)
        if switches_as_lights:
            DEVICE_SETS[CoCoDeviceClass.LIGHTS] = {INTERNAL_KEY_CLASS: CoCoLight,
                                                   INTERNAL_KEY_MODELS: LIST_VALID_LIGHTS + LIST_VALID_SWITCHES}
            DEVICE_SETS[CoCoDeviceClass.SWITCHES] = {INTERNAL_KEY_CLASS: CoCoSwitch, INTERNAL_KEY_MODELS: []}
        # The device control buffer fields
        self._keep_thread_running = True
        self._device_control_buffer = {}
        self._device_control_buffer_size = DEVICE_CONTROL_BUFFER_SIZE
        self._device_control_buffer_command_size = DEVICE_CONTROL_BUFFER_COMMAND_SIZE
        self._device_control_buffer_command_count = 0
        self._device_control_buffer_thread = threading.Thread(target=self._publish_device_control_commands)
        self._device_control_buffer_thread.start()

        if ca_path is None:
            ca_path = os.path.dirname(os.path.realpath(__file__)) + MQTT_CERT_FILE
        client = mqtt.Client(protocol=MQTT_PROTOCOL, transport=MQTT_TRANSPORT)
        _LOGGER.debug(f"mqtt client ok")
        client.username_pw_set(username, password)
        _LOGGER.debug(f"setting user:pass {username}:{password[:3]}...{password[-2:]}")
        client.tls_set(ca_path)
        _LOGGER.debug(f"using ca path == {ca_path} to set up client")
        client.tls_insecure_set(True)
        _LOGGER.debug(f"MQTT client ready")
        self._client = client
        self._address = address
        self._port = port
        self._profile_creation_id = username
        self._all_devices = None
        self._device_callbacks = {}
        self._devices = {}
        self._devices_callback = {}
        self._system_info = None
        self._system_info_callback = lambda x: None
        # refactoring::addition -- alow users to know about errors
        self._error_handlers = []
        # refactoring::suggestion -- the various callback routines sound like either
        #   * some pub/sub event framework could be used  - like https://pypi.org/project/circuits/
        #   * or some Observer could be considered - like https://refactoring.guru/design-patterns/observer/python/example
        _LOGGER.debug(f"Done initializing Coco")

    def __del__(self):
        self.disconnect()

    def connect(self):
        _LOGGER.info(f"connecting ({str(self)})")
        def _on_message(client, userdata, message):
            topic = message.topic
            response = json.loads(message.payload)
            _LOGGER.debug(f"received message ({topic} - {response})")

            # refactoring::suggestion -- better handle these elif dispatch cases through polymorfism + keyed handlers
            #     (i.e. first translate topic into key, would also help readability)
            # refactoring::warning -- code consistency -- using client versus self._client below
            if topic == self._profile_creation_id + MQTT_TOPIC_PUBLIC_RSP and \
                    response[KEY_METHOD] == MQTT_METHOD_SYSINFO_PUBLISH:
                self._system_info = response
                self._system_info_callback(self._system_info)

            elif topic == (self._profile_creation_id + MQTT_TOPIC_SUFFIX_RSP) and \
                    response[KEY_METHOD] == MQTT_METHOD_DEVICES_LIST:
                # refactoring::question why unsubscribe here?  better at event handling layer on top?
                self._client.unsubscribe(self._profile_creation_id + MQTT_TOPIC_SUFFIX_RSP)
                self._process_devices_list(response)

            elif topic == (self._profile_creation_id + MQTT_TOPIC_SUFFIX_SYS_EVT) and \
                    response[KEY_METHOD] == MQTT_METHOD_SYSINFO_PUBLISHED:
                # If the connected controller publishes sysinfo... we expect something to have changed.
                client.subscribe(self._profile_creation_id + MQTT_TOPIC_SUFFIX_RSP, qos=1)
                client.publish(self._profile_creation_id + MQTT_TOPIC_SUFFIX_CMD,
                               json.dumps({KEY_METHOD: MQTT_METHOD_DEVICES_LIST}), 1)

            elif topic == (self._profile_creation_id + MQTT_TOPIC_SUFFIX_EVT) \
                    and (response[KEY_METHOD] == MQTT_METHOD_DEVICES_STATUS or response[
                KEY_METHOD] == MQTT_METHOD_DEVICES_CHANGED):
                devices = extract_devices(response)
                for device in devices:
                    try:
                        if KEY_UUID in device:
                            self._device_callbacks[device[KEY_UUID]][INTERNAL_KEY_CALLBACK](device)
                    except:
                        pass

        def _on_connect(client, userdata, flags, rc):
            if rc == 0:
                _LOGGER.info('Connected!')
                client.subscribe(self._profile_creation_id + MQTT_TOPIC_SUFFIX_RSP, qos=1)
                client.subscribe(self._profile_creation_id + MQTT_TOPIC_PUBLIC_RSP, qos=1)
                client.subscribe(self._profile_creation_id + MQTT_TOPIC_SUFFIX_EVT, qos=1)
                client.subscribe(self._profile_creation_id + MQTT_TOPIC_SUFFIX_SYS_EVT, qos=1)
                client.publish(self._profile_creation_id + MQTT_TOPIC_PUBLIC_CMD,
                               json.dumps({KEY_METHOD: MQTT_METHOD_SYSINFO_PUBLISH}), 1)
                client.publish(self._profile_creation_id + MQTT_TOPIC_SUFFIX_CMD,
                               json.dumps({KEY_METHOD: MQTT_METHOD_DEVICES_LIST}), 1)
            elif MQTT_RC_CODES[rc]:
                # refactoring::addition make sure user can learn about connection failures
                self.notify_error(("Connection Failed", rc, MQTT_RC_CODES[rc]))
                _LOGGER.error(f'Connection Failed - response .code={rc} .msg={MQTT_RC_CODES[rc]}')
                # refactoring::warning --> this does not stop the thread, wrong credentials keep being tried to send messages!
                #     also : this excpetion is ending up in the mqtt thread, not the coco thread
                raise Exception(MQTT_RC_CODES[rc])
            else:
                # refactoring::addition make sure user can learn about connection failures
                self.notify_error(("Connection Failed", rc, None))
                _LOGGER.error(f'Connection Failed with unkown error - response .code={rc}')
                # refactoring::warning --> this does not stop the thread, wrong credentials keep being tried to send messages!
                #     also : this excpetion is ending up in the mqtt thread, not the coco thread
                raise Exception('Unknown error')

        def _on_disconnect(client, userdata, rc):
            _LOGGER.info('Disconnected')
            for uuid, device_callback in self._device_callbacks.items():
                offline = {'Online': 'False', KEY_UUID: uuid}
                device_callback[INTERNAL_KEY_CALLBACK](offline)

        self._client.on_message = _on_message
        self._client.on_connect = _on_connect
        self._client.on_disconnect = _on_disconnect

        self._client.connect_async(self._address, self._port)
        # refactoring::addition -- since disconnect now stops we need this if we disconnect-reconnect in one session
        self._keep_thread_running = True
        self._client.loop_start()
        _LOGGER.debug(f"Coco connect async called and loop started.")

    def disconnect(self):
        # refactoring::addition -- thread not really stopped if flag remains True
        self._keep_thread_running = False
        self._client.loop_stop()
        self._client.disconnect()

    def get_systeminfo(self, callback):
        self._system_info_callback = callback
        if self._system_info:
            self._system_info_callback(self._system_info)

    def get_devices(self, device_class: CoCoDeviceClass, callback: Callable):
        self._devices_callback[device_class] = callback
        if self._devices and device_class in self._devices:
            self._devices_callback[device_class](self._devices[device_class])

    # refactoring::addition -- allow users to know about errors
    def notify_error(self, err):
        for ehfn in self._error_handlers:
            try:
                ehfn(err)
            finally:  # protect propagation from exceptions in handlers
                pass

    # refactoring::suggetsion -- when adopting event framework - we should allow for un-listening too
    # refactoring::addition -- allow users to know about errors
    def on_error(self, ehfn):
        assert callable(ehfn) , "argument to on_error must be callable"
        self._error_handlers.append(ehfn)

    def _publish_device_control_commands(self):
        while self._keep_thread_running:
            device_commands_to_process = None
            sem.acquire()
            if len(self._device_control_buffer.keys()) > 0:
                device_commands_to_process = self._device_control_buffer
            self._device_control_buffer = {}
            self._device_control_buffer_command_count = 0
            sem.release()
            if device_commands_to_process is not None:
                command = process_device_commands(device_commands_to_process)
                self._client.publish(self._profile_creation_id + MQTT_TOPIC_SUFFIX_CMD, json.dumps(command), 1)
            sleep(0.05)

    def _add_device_control(self, uuid, property_key, property_value):
        while len(self._device_control_buffer.keys()) >= self._device_control_buffer_size or \
                self._device_control_buffer_command_count >= self._device_control_buffer_command_size:
            pass
        sem.acquire()
        self._device_control_buffer_command_count += 1
        if uuid not in self._device_control_buffer:
            self._device_control_buffer[uuid] = {}
        self._device_control_buffer[uuid][property_key] = property_value
        sem.release()

    # Processes response on devices.list
    def _process_devices_list(self, response):

        # Only add devices that are actionable
        actionable_devices = list(
            filter(lambda d: d[KEY_TYPE] == DEV_TYPE_ACTION, extract_devices(response)))
        actionable_devices.extend(list(
            filter(lambda d: d[KEY_TYPE] == "thermostat", extract_devices(response))))

        # Only prepare for devices that don't already exist
        # TODO - Can't we do this when we need it (in initialize_devices ?)
        existing_uuids = list(self._device_callbacks.keys())
        for actionable_device in actionable_devices:
            if actionable_device[KEY_UUID] not in existing_uuids:
                self._device_callbacks[actionable_device[KEY_UUID]] = \
                    {INTERNAL_KEY_CALLBACK: None, KEY_ENTITY: None}

        # Initialize
        self.initialize_devices(CoCoDeviceClass.SWITCHED_FANS, actionable_devices)
        self.initialize_devices(CoCoDeviceClass.FANS, actionable_devices)
        self.initialize_devices(CoCoDeviceClass.SWITCHES, actionable_devices)
        self.initialize_devices(CoCoDeviceClass.LIGHTS, actionable_devices)
        self.initialize_devices(CoCoDeviceClass.SHUTTERS, actionable_devices)
        self.initialize_devices(CoCoDeviceClass.THERMOSTATS, actionable_devices)
        self.initialize_devices(CoCoDeviceClass.GENERIC, actionable_devices)

    def initialize_devices(self, device_class, actionable_devices):

        base_devices = [x for x in actionable_devices if x[KEY_MODEL]
                        in DEVICE_SETS[device_class][INTERNAL_KEY_MODELS]]
        if device_class not in self._devices:
            self._devices[device_class] = []
        for base_device in base_devices:
            if self._device_callbacks[base_device[KEY_UUID]] and self._device_callbacks[base_device[KEY_UUID]][
                KEY_ENTITY] and \
                    self._device_callbacks[base_device[KEY_UUID]][KEY_ENTITY].uuid:
                self._device_callbacks[base_device[KEY_UUID]][KEY_ENTITY].update_dev(base_device)
            else:
                self._device_callbacks[base_device[KEY_UUID]][KEY_ENTITY] = \
                    DEVICE_SETS[device_class][INTERNAL_KEY_CLASS](base_device,
                                                                  self._device_callbacks[
                                                                      base_device[
                                                                          KEY_UUID]],
                                                                  self._client,
                                                                  self._profile_creation_id,
                                                                  self._add_device_control)
                self._devices[device_class].append(self._device_callbacks[base_device[KEY_UUID]][KEY_ENTITY])
        if device_class in self._devices_callback:
            self._devices_callback[device_class](self._devices[device_class])
