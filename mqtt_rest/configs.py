import os
from pydantic import BaseModel, ConfigDict, computed_field
from mqtt_rest.utils import get_unique_id, get_internal_ip
from mqtt_rest import __app_name__, __version__


class ServerConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    app_name: str
    app_version: str
    ip: str
    port: int

    @computed_field
    def url(self) -> str:
        return f"http://{self.ip}:{self.port}"

    @computed_field
    def node_id(self) -> str:
        return get_unique_id(self.url)

    @computed_field
    def origin(self) -> dict:
        return {
            "name": self.app_name,
            "sw": self.app_version,
            "url": self.url,
        }


SERVER_CONFIG = ServerConfig(
    app_name=__app_name__,
    app_version=__version__,
    ip=os.environ.get("SERVER_IP", get_internal_ip()),
    port=os.environ.get("SERVER_PORT", 9000),
)


class MQTTConfig(BaseModel):
    broker_ip: str
    broker_port: int
    user: str
    password: str


MQTT_CONFIG = MQTTConfig(
    broker_ip=os.environ.get("BROKER_IP", "localhost"),
    broker_port=os.environ.get("BROKER_PORT", 1883),
    user=os.environ.get("MQTT_USER", "admin"),
    password=os.environ.get("MQTT_PASS", ""),
)
