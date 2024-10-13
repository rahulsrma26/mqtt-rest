import abc
import logging
import time
from typing import Any, Dict, Iterable, Optional, Union

from pydantic import BaseModel, Field

from mqtt_rest.configs import SERVER_CONFIG as CONFIG
from mqtt_rest.mqtt import PROCESSING_DELAY, MQTTBroker
from mqtt_rest.utils import get_unique_id

logger = logging.getLogger("uvicorn.error")
mqttclient = MQTTBroker()


class BaseSensor(BaseModel, abc.ABC):
    name: str
    unique_id: str = Field(serialization_alias="uniq_id")
    bulk_udpate: bool = Field(exclude=True)
    expire_after: Optional[int] = Field(default=None, serialization_alias="exp_aft")
    register_time: Optional[float] = Field(default=None, exclude=True)

    @abc.abstractmethod
    def get_config(self):
        pass

    def append_optional(self, dump: dict) -> dict:
        if self.bulk_udpate:
            dump["val_tpl"] = f"{{{{ value_json.{self.unique_id} }}}}"
        return dump

    @property
    def config_topic(self) -> str:
        component = "binary_sensor" if isinstance(self, BinarySensor) else "sensor"
        return f"homeassistant/{component}/{self.unique_id}/config"

    def get_state_topic(self, device_id: str) -> str:
        if self.bulk_udpate:
            return f"{CONFIG.app_name}/{device_id}/state"
        return f"{CONFIG.app_name}/{self.unique_id}/state"

    def wait_for_register(self):
        if self.register_time:
            remaining = PROCESSING_DELAY - (time.time() - self.register_time)
            if remaining > 0:
                time.sleep(remaining)

    def send_add(self, device_info: dict):
        device_id = device_info["ids"]
        config = self.get_config()
        config["stat_t"] = self.get_state_topic(device_id)
        config["dev"] = device_info
        # MQTT.publish(topic=self.config_topic, payload=config)
        self.wait_for_register()
        mqttclient.publish(topic=self.config_topic, payload=config)
        self.register_time = time.time()

    def send_remove(self):
        # MQTT.publish(topic=self.config_topic)
        self.wait_for_register()
        mqttclient.publish(topic=self.config_topic)
        self.register_time = time.time()


class BinarySensor(BaseSensor):
    value: bool = Field(exclude=True)
    device_class: Optional[str] = Field(default=None, serialization_alias="dev_cla")
    enabled_by_default: Optional[bool] = Field(default=None, serialization_alias="en")

    def get_config(self):
        return self.append_optional(self.model_dump(exclude_none=True, by_alias=True))


class ValueSensor(BaseSensor):
    value: Union[int, float] = Field(exclude=True)
    device_class: Optional[str] = Field(default=None, serialization_alias="dev_cla")
    unit: Optional[str] = Field(default=None, serialization_alias="unit_of_meas")
    state_class: Optional[str] = Field(default=None, serialization_alias="stat_cla")

    def get_config(self):
        return self.append_optional(self.model_dump(exclude_none=True, by_alias=True))


# class EnumSensor(BaseSensor):
#     value: str = Field(exclude=True)
#     options: list[str] = Field(serialization_alias="ops")

#     def get_config(self):
#         result = self.model_dump(exclude_none=True, by_alias=True)
#         result["dev_cla"] = "enum"
#         return result


class DiagnosticSensor(BaseSensor):
    value: str = Field(exclude=True)

    def get_config(self):
        result = self.append_optional(self.model_dump(exclude_none=True, by_alias=True))
        result["ent_cat"] = "diagnostic"
        return result


class Device:
    def __init__(
        self,
        name: str,
        model: Optional[str] = None,
        configuration_url: Optional[str] = None,
        via_device: Optional[str] = None,
        expire_after: Optional[int] = None,
    ):
        self.name = name
        self.model = model or "generic"
        self.id = get_unique_id(self.name + self.model)
        self.configuration_url = configuration_url
        self.via_device = via_device
        self.expire_after = expire_after
        self.discovered = False
        self.sensors = {}

    def get_config(self):
        dump = {
            "name": self.name,
            "id": self.id,
            "model": self.model,
            "discovered": self.discovered,
        }
        if self.configuration_url:
            dump["configuration_url"] = self.configuration_url
        if self.via_device:
            dump["via_device"] = self.via_device
        if self.expire_after:
            dump["expire_after"] = self.expire_after
        dump["sensors"] = {name: sensor.get_config() for name, sensor in self.sensors.items()}
        return dump

    def _create_sensor(self, name: str, value: Any, bulk: bool, **kwargs) -> BaseSensor:
        kwargs["name"] = name
        kwargs["unique_id"] = get_unique_id(self.id + name)
        kwargs["bulk_udpate"] = bulk
        kwargs["value"] = value
        if self.expire_after and "expire_after" not in kwargs:
            kwargs["expire_after"] = self.expire_after
        if isinstance(value, bool):
            return BinarySensor(**kwargs)
        if isinstance(value, (int, float)):
            return ValueSensor(**kwargs)
        kwargs["value"] = str(value)
        return DiagnosticSensor(**kwargs)

    def _get_device_info(self):
        if self.discovered:
            return {"ids": self.id}
        self.discovered = True
        info = {
            "name": self.name,
            "mdl": self.model,
            "mf": CONFIG.app_name,
            "sw": CONFIG.app_version,
            "ids": self.id,
        }
        if self.configuration_url:
            info["cu"] = self.configuration_url
        if self.via_device:
            info["via_device"] = self.via_device
        return info

    def remove_sensor(self, name: str):
        logger.info(f"Removing sensor {name} ({self.name})")
        if sensor := self.sensors.pop(name):
            sensor.send_remove()

    def get_sensor(self, name: str, value: Any, bulk: bool, **kwargs) -> BaseSensor:
        if sensor := self.sensors.get(name):
            if not isinstance(sensor.value, type(value)):
                logger.warning(
                    f"Sensor {name} ({self.name}) value type changed from {type(sensor.value)} to {type(value)}"
                )
                self.remove_sensor(name)
            elif sensor.bulk_udpate != bulk:
                logger.warning(
                    f"Sensor {name} ({self.name}) bulk update changed from {sensor.bulk_udpate} to {bulk}"
                )
                self.remove_sensor(name)
            else:
                return sensor

        logger.info(f"Registering sensor {name} ({self.name})")
        sensor = self._create_sensor(name, value, bulk, **kwargs)
        self.sensors[name] = sensor
        sensor.send_add(self._get_device_info())
        return sensor

    def update(self, name: str, value: Any):
        sensor = self.get_sensor(name, value, bulk=False)
        if isinstance(value, bool):
            value = "ON" if value else "OFF"
        # MQTT.publish(topic=sensor.get_state_topic(self.id), payload=value)
        sensor.wait_for_register()
        mqttclient.publish(topic=sensor.get_state_topic(self.id), payload=value)

    def bulk_update(self, data: Dict[str, Any]):
        values, topic, newest = {}, None, 0.0
        for name, value in data.items():
            sensor = self.get_sensor(name, value, bulk=True)
            newest = max(newest, sensor.register_time or 0)
            if not topic:
                topic = sensor.get_state_topic(self.id)
            if isinstance(value, bool):
                value = "ON" if value else "OFF"
            values[sensor.unique_id] = value
        if topic:
            # MQTT.publish(topic=topic, payload=values)
            remaining = PROCESSING_DELAY - (time.time() - newest)
            if remaining > 0:
                time.sleep(remaining)
            mqttclient.publish(topic=topic, payload=values)

    def bulk_remove(self, names: Optional[Iterable[str]] = None):
        if not names:
            names = list(self.sensors.keys())
        for name in names:
            self.remove_sensor(name)
