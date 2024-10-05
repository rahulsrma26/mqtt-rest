import logging
from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse
from mqtt_rest.plugins.helper import helper_templates
from mqtt_rest.plugins.sensors.parser import parse_sensors
from mqtt_rest.db import add_device, get_device, remove_device

PLUGIN_NAME = "sensors"
logger = logging.getLogger("uvicorn.error")
router = APIRouter(prefix=f"/{PLUGIN_NAME}")
last_report = {}


def get_device_name(name: str):
    name = name.replace(" ", "_")
    return f"{name} {PLUGIN_NAME}"


@router.get("/install")
async def get_install(request: Request):
    return helper_templates.TemplateResponse(
        "install.sh", {"request": request, "dependencies": "sensors"}
    )


@router.get("/manager")
async def get_manager(request: Request):
    return helper_templates.TemplateResponse(
        "single_job.sh", {"request": request, "data_command": "sensors"}
    )


@router.put("/submit/{name}")
async def submit(request: Request, name: str, expiry: int = 3600):
    global last_report
    device_name = get_device_name(name)
    last_report[device_name] = (await request.body()).decode()
    values = parse_sensors(last_report[device_name])
    device = get_device(device_name, create=False)
    if not device:
        configuration_url = str(request.url).replace("/submit/", "/report/")
        device = add_device(
            name=device_name,
            model="mqtt-plugin",
            configuration_url=configuration_url,
            expire_after=expiry,
        )
        for key, value in values.items():
            device.get_sensor(key, value, bulk=True, unit="°C")
        device.get_sensor("ip", "detecting...", bulk=False)
    device.bulk_update(values)
    device.update("ip", str(request.client.host))


@router.delete("/delete/{name}")
async def delete(name: str):
    global last_report
    device_name = get_device_name(name)
    last_report.pop(device_name)
    remove_device(device_name)


@router.get("/report/{name}", response_class=PlainTextResponse)
async def report(name: str):
    return last_report.get(get_device_name(name))
