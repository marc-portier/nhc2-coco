from .coco_entity import CoCoEntity
from .const import KEY_POSITION, VALUE_OPEN, VALUE_STOP, VALUE_CLOSE, KEY_ACTION
from .helpers import extract_property_value_from_device


class CoCoShutter(CoCoEntity):

    @property
    def position(self):
        return self._position

    def __init__(self, dev, callback_container, client, profile_creation_id, command_device_control):
        super().__init__(dev, callback_container, client, profile_creation_id, command_device_control)
        self._position = None
        self.update_dev(dev, callback_container)

    # refactoring::addition allow entities to represent themselves as string
    def __str__(self):
        state_str = f"@{self.position:=+4d}"
        return super(CoCoShutter, self).__str__() + ' ' + state_str

    def open(self):
        self._command_device_control(self._uuid, KEY_ACTION, VALUE_OPEN)

    def stop(self):
        self._command_device_control(self._uuid, KEY_ACTION, VALUE_STOP)

    def close(self):
        self._command_device_control(self._uuid, KEY_ACTION, VALUE_CLOSE)

    def set_position(self, position: int):
        self._command_device_control(self._uuid, KEY_POSITION, str(position))

    def update_dev(self, dev, callback_container=None):
        has_changed = super().update_dev(dev, callback_container)
        position_value = extract_property_value_from_device(dev, KEY_POSITION)
        if position_value is not None and self._position != int(position_value):
            self._position = int(position_value)
            has_changed = True
        return has_changed

    def _update(self, dev):
        has_changed = self.update_dev(dev)
        if has_changed:
            self._state_changed()

    def request_state_change(self, newstate):
        position = int(newstate)
        assert str(position) == newstate, "requested position should be a valid integer"  # roundtrip testing
        # refactoring::suggestion -- need to investigate what min max boundaries apply to valid shutter-positions
        self.set_position(position)
