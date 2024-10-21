"""
This module contains the routes for the smartctl plugin.
"""

import logging

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

from mqtt_rest.db import add_device, get_device, remove_device
from mqtt_rest.plugins.helper import (
    JOB_FREQUENCY_HOUR_DAY,
    BashFunction,
    Command,
    Installer,
    SingleJob,
)
from mqtt_rest.plugins.smartwrt.parsers import parse_report

PLUGIN_NAME = "smartwrt"
logger = logging.getLogger("uvicorn.error")
router = APIRouter(prefix=f"/{PLUGIN_NAME}")
last_report = {}


def get_device_name(name: str):
    name = name.replace(" ", "_")
    return f"{name} {PLUGIN_NAME}"


def get_job_func() -> BashFunction:
    return BashFunction(
        body="""
        smartwrt
        """,
        name="run_job",
    )


@router.get("/install")
async def get_install(request: Request):
    return Installer(
        url=str(request.url),
        dependencies=[
            Command(
                command="smartctl",
                install_func=BashFunction(
                    body="""
                    apt install -y smartmontools && systemctl enable smartd
                    """,
                ),
            ),
            Command(
                command="smartwrt",
                install_func=BashFunction(
                    body="""
                    wget -qLO /usr/local/sbin/smartwrt https://github.com/rahulsrma26/scripts/raw/main/manage/debian/smartwrt.sh
                    chmod +x /usr/local/sbin/smartwrt
                    """
                ),
            ),
        ],
        description="""
        This plugin uses the "smartctl" command to get the amount of data written to the disk.
        """,
    ).render()


@router.get("/manager")
async def get_manager(request: Request):
    return SingleJob(
        url=str(request.url),
        job_func=get_job_func(),
        freq2cron_func=JOB_FREQUENCY_HOUR_DAY,
    ).render()


@router.put("/submit/{name}")
async def submit(request: Request, name: str):
    global last_report
    device_name = get_device_name(name)
    last_report[device_name] = (await request.body()).decode()
    values = parse_report(last_report[device_name])
    device = get_device(device_name, create=False)
    if not device:
        configuration_url = str(request.url).replace("/submit/", "/report/")
        device = add_device(
            name=device_name,
            model="mqtt-plugin",
            configuration_url=configuration_url,
        )
        for key, value in values.items():
            device.get_sensor(key, value, bulk=True, unit="GiB")
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
