


class Nhc2MsgLayout:
    pass


class Nhc2MsgLayoutNone(Nhc2MsgLayout):
    """ Layout for basic message with No parameters
    """
    pass


class Nhc2MsgLayoutError(Nhc2MsgLayout):
    """ Layout for errors:
    {
        "ErrMessage": "Method 'unknown' not supported for topic 'hobby/control/devices/cmd'",
        "ErrCode": "UNKNOWN_METHOD",
        "Method": "unknown"
    }
    """
    pass


class Nhc2MsgLayoutDeviceDetails(Nhc2MsgLayout):
    """ Layout for device lists:
    {
        "Params": [{
            "Devices": [{
                "Name": "Dimmable lamp",
                "Uuid": "21a967a1-676d-487b-b8d4-9736ef16d450",
                "Identifier": "a4fafca1-bde4-4ad7-94f9-292c60c26bf7",
                "Online": "True",
                "Technology": "nikohomecontrol",
                "Type": "action",
                "Model": "dimmer",
                "Properties": [
                    {"Brightness": "100" },
                    {"Status": "Off" },
                    {"Aligned": "True" }],
                "PropertyDefinitions": [
                    {"Brightness": {
                        "Description": "Range(0.00,100.00,1.00)",
                        "HasStatus": "true",
                        "CanControl": "true"
                    }},
                    {"Status": {
                        "Description": "Choice(On,Off)",
                        "HasStatus": "true",
                        "CanControl": "true"
                    }},
                    {"Aligned": {
                        "Description": "Boolean",
                        "HasStatus": "true",
                        "CanControl": "false"
                    }}
                ],
                "Traits": [],
                "Parameters": [
                    {"LocationId": "7f62f934-83d3-4c66-b4bd-df7065cb1c6a" },
                    {"LocationName": "Demo" },
                    {"LocationIcon": "general" }
                ]
            }]
        }]
    }
    """
    pass


class Nhc2MsgLayoutDeviceDetails(Nhc2MsgLayout):
    """ Layout for device-id lists:
    {
        "Params": [{
            "Devices": [
                {"Uuid": "ab2e315e-a6df-4cc8-9518-5fa2a48226f5"},
                {"Uuid": "ae56f142-03ca-4de6-8547-282489a615ca"}
            ]
        }]
    }
    """
    pass
