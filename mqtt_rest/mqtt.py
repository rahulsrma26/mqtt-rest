from typing import Union
import logging
import json
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
from mqtt_rest.configs import MQTT_CONFIG as CONFIG

logger = logging.getLogger("uvicorn.error")


class MQTT:
    @staticmethod
    def publish(topic: str, payload: Union[str, dict] = "", retain: bool = False, qos: int = 0):
        logger.debug(f"Publishing to {topic} (retain={retain}, qos={qos})")
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        if not isinstance(payload, (int, float, str)):
            raise ValueError("Payload must be a string, int, or float")
        logger.debug(f"payload: {payload}")
        publish.single(
            topic,
            payload=payload,
            qos=qos,
            retain=retain,
            hostname=CONFIG.broker_ip,
            port=CONFIG.broker_port,
            auth={"username": CONFIG.user, "password": CONFIG.password},
            keepalive=60,
            protocol=mqtt.MQTTv31,
        )
