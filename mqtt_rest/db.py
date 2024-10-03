from typing import Optional
from mqtt_rest.device import Device
from mqtt_rest.configs import SERVER_CONFIG as CONFIG

SOURCE_DEVICE = None
SOURCE_DEVICE_NAME = "devices"
all_devices = {}


def add_source_device():
    global SOURCE_DEVICE, SOURCE_DEVICE_NAME, all_devices
    SOURCE_DEVICE = Device(
        name=CONFIG.app_name,
        model="Server",
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
    device = Device(name=name, via_device=SOURCE_DEVICE.id)
    all_devices[name] = device
    SOURCE_DEVICE.update(SOURCE_DEVICE_NAME, value=len(all_devices))
    return device


def remove_device(name: str):
    global SOURCE_DEVICE, SOURCE_DEVICE_NAME, all_devices
    device = all_devices.pop(name, None)
    if device:
        device.bulk_remove()
        SOURCE_DEVICE.update(SOURCE_DEVICE_NAME, value=len(all_devices))