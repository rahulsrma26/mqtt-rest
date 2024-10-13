"""
This module contains the routes for the sensors plugin.
"""

import logging

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

from mqtt_rest.db import add_device, get_device, remove_device
from mqtt_rest.plugins.helper import (
    JOB_FREQUENCY_MINUTE_HOUR_DAY,
    BashFunction,
    Command,
    Installer,
    SingleJob,
)
from mqtt_rest.plugins.sensors.parsers import parse_sensors

PLUGIN_NAME = "sensors"
logger = logging.getLogger("uvicorn.error")
router = APIRouter(prefix=f"/{PLUGIN_NAME}")
last_report = {}


def get_device_name(name: str):
    name = name.replace(" ", "_")
    return f"{name} {PLUGIN_NAME}"


@router.get("/install")
async def get_install(request: Request):
    return Installer(
        url=str(request.url),
        dependencies=[Command(command="sensors", package="lm-sensors")],
        description="""
        This plugin uses the "sensors" command to get the temperature of the CPU and other sensors.
        """,
    ).render()


@router.get("/manager")
async def get_manager(request: Request):
    return SingleJob(
        url=str(request.url),
        run_job=BashFunction(
            name="run_job",
            body="""
            sensors
            """,
        ),
        get_cron_frequency=JOB_FREQUENCY_MINUTE_HOUR_DAY,
    ).render()


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
