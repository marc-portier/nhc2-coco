import random
import string
from util4tests import run_single_test, log, random_passwd
from nhc2_coco.mqtt import (
    Nhc2MQTopic, Nhc2MQConnector, Nhc2MQService, Nhc2MQMessageClass, Nhc2MQMessageType,
    Nhc2Connection,
)


def test_nhc2_mqtt_topic():
    log.debug("starting test of topic formatting")
    ctrl_devs = Nhc2MQTopic(Nhc2MQConnector.HOBBY, Nhc2MQService.CONTROL, Nhc2MQMessageClass.DEVICES, Nhc2MQMessageType.CMD)
    assert ctrl_devs.path == 'hobby/control/devices/cmd', "Topic path should concatenate the parts"
    assert ctrl_devs.method.name == 'PUBLISH', "cmd topics are expected to be used with the publish method"

    sys_evt = Nhc2MQTopic(Nhc2MQConnector.HOBBY, Nhc2MQService.SYSTEM, None, Nhc2MQMessageType.EVT)
    assert sys_evt.path == 'hobby/system/evt', "Topic path should concatenate the parts and skip the None parts"
    assert sys_evt.method.name == 'SUBSCRIBE', "evt topics are expected to be used with the subscribe method"


def test_nhc2_connection():
    log.debug("starting test of connection class")
    myhost, mypass = "myhost.local", random_passwd()
    conn = Nhc2Connection(myhost, mypass)
    conn_params = conn.as_tuple()
    assert conn_params[0] == myhost
    assert conn_params[1] == mypass
    assert conn_params[2] == 8884
    assert conn_params[3].endswith(Nhc2Connection.CERTFILE_NAME)


if __name__ == "__main__":
    run_single_test(__file__)
