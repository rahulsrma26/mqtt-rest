from typing import Union, Any, Tuple
from unittest import mock
import pytest
from mqtt_rest.device import Device
from mqtt_rest.configs import SERVER_CONFIG as CONFIG


class MockedMQTT:
    calls = []

    @staticmethod
    def publish(topic: str, payload: Union[str, dict] = "", *args, **kwargs):
        MockedMQTT.calls.append((topic, payload))


test_single_sensor = [
    (False, "binary_sensor", "OFF"),
    (True, "binary_sensor", "ON"),
    (0, "sensor", 0),
    (10, "sensor", 10),
    (10.5, "sensor", 10.5),
    ("text", "sensor", "text"),
]


def msg_helper(
    call: Tuple[str, Any],
    device: str,
    sensor: str,
    component: str,
    first: bool = False,
    bulk: bool = False,
    remove: bool = False,
):
    topic, msg = call
    path = topic.split("/")
    assert len(path) == 4
    assert path[0] == "homeassistant"
    assert path[1] == component
    assert path[3] == "config"
    id = path[2]
    if remove:
        assert msg == ""
        return id, None
    assert isinstance(msg, dict)
    assert msg.get("name") == sensor
    assert msg.get("uniq_id") == id
    dev = msg.get("dev")
    assert dev is not None
    assert "ids" in dev
    device_id = dev["ids"]
    if first:
        assert dev.get("name") == device
    if bulk:
        path = msg.get("stat_t")
        assert path is not None
        path = path.split("/")
        assert len(path) == 3
        assert path[0] == CONFIG.app_name
        assert path[1] == device_id
        assert path[2] == "state"
        value_template = msg.get("val_tpl")
        assert value_template is not None
        assert value_template == f"{{{{ value_json.{id} }}}}"
    else:
        assert msg.get("stat_t") == f"{CONFIG.app_name}/{id}/state"
    return id, device_id


@pytest.mark.parametrize("value,component,expected", test_single_sensor)
@mock.patch(f"mqtt_rest.device.MQTT.publish", MockedMQTT.publish)
def test_single_sensor(value, component, expected):
    MockedMQTT.calls = []
    dev = Device(name="test-device")
    dev.update("test-sensor", value)
    dev.remove_sensor("test-sensor")
    calls = MockedMQTT.calls
    assert len(calls) == 3
    id, _ = msg_helper(calls[0], "test-device", "test-sensor", component, first=True)
    topic, msg = calls[1]
    assert topic == f"{CONFIG.app_name}/{id}/state"
    assert msg == expected
    nid, _ = msg_helper(calls[2], "test-device", "test-sensor", component, remove=True)
    assert id == nid, "ID changed after remove"


@mock.patch(f"mqtt_rest.device.MQTT.publish", MockedMQTT.publish)
def test_multiple_sensors():
    MockedMQTT.calls = []
    dev = Device(name="test-device")
    sensors = {
        "sensor-1": True,
        "sensor-2": False,
        "sensor-3": 0,
        "sensor-4": 10,
        "sensor-5": 10.5,
        "sensor-6": "text",
    }
    dev.bulk_update(sensors)
    dev.bulk_remove()
    calls = MockedMQTT.calls
    assert len(calls) == 6 + 1 + 6
    dev_id = None
    msg = {}
    for i, (k, v) in enumerate(sensors.items()):
        comp = "binary_sensor" if isinstance(v, bool) else "sensor"
        id, d = msg_helper(calls[i], "test-device", k, comp, first=i == 0, bulk=True)
        if dev_id is None:
            dev_id = d
        else:
            assert dev_id == d, f"Device ID changed for sensor {i} ({k})"
        if isinstance(v, bool):
            v = "ON" if v else "OFF"
        msg[id] = v
    assert calls[6][0] == f"{CONFIG.app_name}/{dev_id}/state"
    assert calls[6][1] == msg
    for i, (k, v) in enumerate(sensors.items()):
        comp = "binary_sensor" if isinstance(v, bool) else "sensor"
        id, _ = msg_helper(calls[7 + i], "test-device", k, comp, remove=True, bulk=True)
        assert id in msg, f"Sensor {k} not found in bulk remove"
        msg.pop(id)
    assert not msg, "Not all sensors were removed"