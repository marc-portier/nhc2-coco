from enum import Enum
from typing import NamedTuple
from .mq-const import Nhc2MQTopic, Nhc2MQConnector, Nhc2MQService, Nhc2MQMessageClass, Nhc2MQMessageType


class Nhc2APIMessageModel(NamedTuple):
    message_type: Nhc2MQMessageType
    method: str
    layout_class: type


class Nhc2APIFunctionModel(NamedTuple):
    service: Nhc2MQService
    message_class: Nhc2MQMessageClass
    message_models: list


class Nhc2APIFunction(Enum):
    CONTROL_DEVICES = Nhc2APIFunctionModel( Nhc2MQService.CONTROL, Nhc2MQMessageClass.DEVICES,
        Nhc2APIMessageModel( Nhc2MQMessageType.CMD, "devices.list", Nhc2MsgLayoutNone),
        Nhc2APIMessageModel( Nhc2MQMessageType.RSP, "devices.list", Nhc2MsgLayoutDeviceDetails),
        Nhc2APIMessageModel( Nhc2MQMessageType.ERR, "devices.list", Nhc2MsgLayoutError),

        Nhc2APIMessageModel( Nhc2MQMessageType.EVT, "devices.added", Nhc2MsgLayoutDeviceDetails),
        Nhc2APIMessageModel( Nhc2MQMessageType.EVT, "devices.removed", Nhc2MsgLayoutDeviceIDs),
        Nhc2APIMessageModel( Nhc2MQMessageType.EVT, "devices.displayname_changed", TODO_LAYOUT),
        Nhc2APIMessageModel( Nhc2MQMessageType.EVT, "devices.changed", TODO_LAYOUT),
        Nhc2APIMessageModel( Nhc2MQMessageType.EVT, "devices.param_changed", TODO_LAYOUT),

        Nhc2APIMessageModel( Nhc2MQMessageType.CMD, "devices.control", TODO_LAYOUT),
        Nhc2APIMessageModel( Nhc2MQMessageType.RSP, "devices.control", TODO_LAYOUT),
        Nhc2APIMessageModel( Nhc2MQMessageType.ERR, "devices.control", TODO_LAYOUT),

        Nhc2APIMessageModel( Nhc2MQMessageType.EVT, "devices.status", TODO_LAYOUT),
    )
    CONTROL_LOCATIONS = Nhc2APIFunctionModel( Nhc2MQService.CONTROL, Nhc2MQMessageClass.LOCATIONS,
        Nhc2APIMessageModel( Nhc2MQMessageType.CMD, "locations.list", TODO_LAYOUT),
        Nhc2APIMessageModel( Nhc2MQMessageType.RSP, "locations.list", TODO_LAYOUT),
        Nhc2APIMessageModel( Nhc2MQMessageType.ERR, "locations.list", TODO_LAYOUT),

        Nhc2APIMessageModel( Nhc2MQMessageType.CMD, "locations.listitems", TODO_LAYOUT),
        Nhc2APIMessageModel( Nhc2MQMessageType.RSP, "locations.listitems", TODO_LAYOUT),
        Nhc2APIMessageModel( Nhc2MQMessageType.ERR, "locations.listitems", TODO_LAYOUT),
    )
    SYSTEM = Nhc2APIFunctionModel( Nhc2MQService.SYSTEM, None,
        Nhc2APIMessageModel( Nhc2MQMessageType.EVT, "time.published", TODO_LAYOUT),
        Nhc2APIMessageModel( Nhc2MQMessageType.EVT, "systeminfo.publish", TODO_LAYOUT),
    )
    NOTIFICATION = Nhc2APIFunctionModel( Nhc2MQService.NOTIFICATION, None,
        Nhc2APIMessageModel( Nhc2MQMessageType.CMD, "notifications.list", Nhc2MsgLayoutNone),
        Nhc2APIMessageModel( Nhc2MQMessageType.RSP, "notifications.list", Nhc2MsgLayoutDeviceDetails),
        Nhc2APIMessageModel( Nhc2MQMessageType.ERR, "notifications.list", Nhc2MsgLayoutError),

        Nhc2APIMessageModel( Nhc2MQMessageType.CMD, "notifications.update", Nhc2MsgLayoutNone),
        Nhc2APIMessageModel( Nhc2MQMessageType.RSP, "notifications.update", Nhc2MsgLayoutDeviceDetails),
        Nhc2APIMessageModel( Nhc2MQMessageType.ERR, "notifications.update", Nhc2MsgLayoutError),

        Nhc2APIMessageModel( Nhc2MQMessageType.EVT, "notifications.raised", TODO_LAYOUT),
    )
