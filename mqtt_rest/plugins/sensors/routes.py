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


@router.put("/submit/{device_name}")
async def submit(request: Request, device_name: str, expiry: int = 3600):
    global last_report
    last_report[device_name] = (await request.body()).decode()
    values = parse_sensors(last_report[device_name])
    device = get_device(device_name, create=False)
    if not device:
        configuration_url = str(request.url).replace("/submit/", "/report/")
        device = add_device(
            name=f"{device_name}-{PLUGIN_NAME}",
            model="mqtt-plugin",
            configuration_url=configuration_url,
            expire_after=expiry,
        )
    device.bulk_update(values)


@router.delete("/delete/{device_name}")
async def delete(device_name: str):
    global last_report
    last_report.pop(device_name)
    remove_device(device_name)


@router.get("/report/{device_name}", response_class=PlainTextResponse)
async def report(device_name: str):
    return last_report.get(device_name)
