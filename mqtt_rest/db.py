import logging
from typing import Annotated, Optional

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from mqtt_rest.configs import SERVER_CONFIG as CONFIG
from mqtt_rest.device import Device

SOURCE_DEVICE = None
SOURCE_DEVICE_NAME = "devices"
all_devices = {}

logger = logging.getLogger("uvicorn.error")

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def add_source_device():
    global SOURCE_DEVICE, SOURCE_DEVICE_NAME, all_devices
    SOURCE_DEVICE = Device(
        name=CONFIG.app_name,
        model=f"Server ({CONFIG.ip}:{CONFIG.port})",
        configuration_url=CONFIG.url + "/docs",
    )
    SOURCE_DEVICE.update(SOURCE_DEVICE_NAME, value=len(all_devices))


def remove_source_device():
    global SOURCE_DEVICE
    SOURCE_DEVICE.bulk_remove()
    SOURCE_DEVICE = None


def add_device(*args, **kwargs) -> Device:
    global SOURCE_DEVICE, SOURCE_DEVICE_NAME, all_devices
    kwargs["via_device"] = SOURCE_DEVICE.id
    logger.info(f"Adding device {kwargs['name']}")
    device = Device(*args, **kwargs)
    all_devices[device.name] = device
    SOURCE_DEVICE.update(SOURCE_DEVICE_NAME, value=len(all_devices))
    return device


def get_device(name: str, create: bool = True) -> Optional[Device]:
    global SOURCE_DEVICE, SOURCE_DEVICE_NAME, all_devices
    if name in all_devices:
        return all_devices[name]
    if not create:
        return None
    return add_device(name=name)


def remove_device(name: str):
    global SOURCE_DEVICE, SOURCE_DEVICE_NAME, all_devices
    device = all_devices.pop(name, None)
    if device:
        logger.info(f"Removing device {name}")
        device.bulk_remove()
        SOURCE_DEVICE.update(SOURCE_DEVICE_NAME, value=len(all_devices))
