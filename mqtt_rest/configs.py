import os
from typing import Any, Callable, Optional, Union

from pydantic import BaseModel, ConfigDict, computed_field

from mqtt_rest import __app_name__, __version__
from mqtt_rest.utils import get_internal_ip, get_unique_id


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


def get_env(name: str, defaut: Union[Any, Callable[[], Optional[Any]]]) -> Any:
    ip = os.environ.get(name)
    if not ip:
        if callable(defaut):
            ip = defaut()
        else:
            ip = defaut
    return ip


SERVER_CONFIG = ServerConfig(
    app_name=__app_name__,
    app_version=__version__,
    ip=get_env("SERVER_IP", get_internal_ip),
    port=get_env("SERVER_PORT", 9000),
)


class MQTTConfig(BaseModel):
    broker_ip: str
    broker_port: int
    user: str
    password: str
    enable_logger: bool


MQTT_CONFIG = MQTTConfig(
    broker_ip=get_env("BROKER_IP", "localhost"),
    broker_port=get_env("BROKER_PORT", 1883),
    user=get_env("MQTT_USER", "admin"),
    password=get_env("MQTT_PASS", ""),
    enable_logger=get_env("MQTT_LOG", "F").upper()[0] == "T",
)
