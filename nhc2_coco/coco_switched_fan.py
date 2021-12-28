from .coco_entity import CoCoEntity
from .const import KEY_STATUS, VALUE_ON, VALUE_OFF
from .helpers import extract_property_value_from_device


class CoCoSwitchedFan(CoCoEntity):

    @property
    def is_on(self):
        return self._is_on

    def __init__(self, dev, callback_container, client, profile_creation_id, command_device_control):
        super().__init__(dev, callback_container, client, profile_creation_id, command_device_control)
        self._is_on = None
        self.update_dev(dev, callback_container)

    # refactoring::addition allow entities to represent themselves as string
    def __str__(self):
        state_str = 'ON' if self.is_on else 'OFF'
        return super(CoCoSwitchedFan, self).__str__() + ' ' + state_str

    def turn_on(self):
        self._command_device_control(self._uuid, KEY_STATUS, VALUE_ON)

    def turn_off(self):
        self._command_device_control(self._uuid, KEY_STATUS, VALUE_OFF)

    def update_dev(self, dev, callback_container=None):
        has_changed = super().update_dev(dev, callback_container)
        status_value = extract_property_value_from_device(dev, KEY_STATUS)
        if status_value and self._is_on != (status_value == VALUE_ON):
            self._is_on = (status_value == VALUE_ON)
            has_changed = True
        return has_changed

    def _update(self, dev):
        has_changed = self.update_dev(dev)
        if has_changed:
            self._state_changed()

    def request_state_change(self, newstate):
        def request_state_change(self, newstate):
            state_options = ['on', 'off', 'toggle']
            assert newstate in state_options, f"Switch newstate must be one of {state_options}"
            if newstate == 'toggle':
                newstate = 'off' if self._is_on else 'on'
            if newstate == 'on':
                self.turn_on()
            else:
                self.turn_off()
