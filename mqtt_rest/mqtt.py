import json
import logging
import time
from threading import Lock
from typing import Union

import paho.mqtt.client as mqtt

from mqtt_rest.configs import MQTT_CONFIG, SERVER_CONFIG

logger = logging.getLogger("uvicorn.error")
PROCESSING_DELAY = 0.2


class SingletonMeta(type):
    """
    This is a thread-safe implementation of Singleton.
    see: https://refactoring.guru/design-patterns/singleton/python/example#example-1
    """

    _instances = {}
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class MQTTBroker(metaclass=SingletonMeta):
    client: mqtt.Client = None
    is_connected: bool = False

    def __init__(self) -> None:
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=SERVER_CONFIG.url,
            clean_session=1,
            protocol=mqtt.MQTTv311,
            transport="tcp",
            reconnect_on_failure=True,
        )
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.username_pw_set(MQTT_CONFIG.user, MQTT_CONFIG.password)
        if MQTT_CONFIG.enable_logger:
            self.client.enable_logger(logger)

    def _on_connect(self, client, userdata, flags, rc, properties):
        if rc == 0:
            self.is_connected = True
            logger.info("Connected to MQTT Broker")
        else:
            logger.error(f"Failed to connect to MQTT Broker with code {rc}")

    def _on_disconnect(self, client, userdata, flags, rc, properties):
        self.is_connected = False
        logger.warning(f"Disconnected from MQTT Broker with code {rc}")

    def connect(self):
        if self.is_connected:
            logger.warning("Already connected to MQTT Broker (connect ignored)")
            return

        self.client.connect(
            host=MQTT_CONFIG.broker_ip,
            port=MQTT_CONFIG.broker_port,
            keepalive=3600,
        )
        self.client.loop_start()

        for i in range(10):
            if self.is_connected:
                break
            logger.info("Waiting for connection to MQTT Broker")
            time.sleep(1)
        else:
            logger.error("Failed to connect to MQTT Broker")
            self.client.loop_stop()
            return False
        return True

    def disconnect(self):
        if not self.is_connected:
            logger.warning("Not connected to MQTT Broker (disconnect ignored)")
            return
        time.sleep(PROCESSING_DELAY)  # wait for all messages to be sent
        self.client.disconnect()
        self.client.loop_stop()

    def publish(
        self, topic: str, payload: Union[str, dict] = "", retain: bool = False, qos: int = 1
    ):
        logger.debug(f"Publishing to {topic} (retain={retain}, qos={qos})")
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        if not isinstance(payload, (int, float, str)):
            raise ValueError("Payload must be a string, int, or float")
        logger.debug(f"payload: {payload}")
        self.client.publish(topic, payload=payload, qos=qos, retain=retain)
