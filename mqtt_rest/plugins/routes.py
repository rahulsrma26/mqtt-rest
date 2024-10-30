import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

from mqtt_rest import db
from mqtt_rest.plugins import report_manager as rm
from mqtt_rest.plugins.simple_plugin import SimplePlugin
from mqtt_rest.plugins.simple_plugins import PLUGINS

logger = logging.getLogger("uvicorn.error")
router = APIRouter()
plugin_names = list(PLUGINS.keys())


def get_plugin(name: str) -> SimplePlugin:
    plugin = PLUGINS.get(name)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    if not isinstance(plugin, SimplePlugin):
        raise HTTPException(
            status_code=500, detail=f"Plugin is not a SimplePlugin but {type(plugin)}"
        )
    return plugin


def get_device_name(plugin: str, device: str) -> str:
    return f'{device.replace(" ", "_")} ({plugin})'


@router.get("/plugins/{plugin}/install")
async def get_install(request: Request, plugin: str):
    return get_plugin(plugin).install.render(str(request.url))


@router.get("/plugins/{plugin}/manager")
async def get_manager(request: Request, plugin: str):
    return get_plugin(plugin).manager.render(str(request.url))


@router.put("/plugins/{plugin}/devices/{name}/submit")
async def put_submit(request: Request, plugin: str, name: str, session: db.SessionDep):
    device_name = get_device_name(plugin, name)
    result = (await request.body()).decode()
    sensors = get_plugin(plugin).parser(result)
    device = db.get_device(device_name, create=False)
    if not device:
        device = db.add_device(
            name=device_name,
            model="mqtt-plugin",
            configuration_url=str(request.url).rsplit("/", 1)[0] + "/report",
        )
        for key, sv in sensors.items():
            device.get_sensor(key, sv.value, bulk=True, unit=sv.unit)
        device.get_sensor("ip", "detecting...", bulk=False)
    device.bulk_update({key: sv.value for key, sv in sensors.items()})
    client_ip = str(request.client.host)
    device.update("ip", client_ip)
    return rm.update_report(
        session, rm.Report(plugin=plugin, device=device_name, incoming_ip=client_ip, result=result)
    )


@router.get("/plugins/{plugin}/devices/{name}/report", response_class=PlainTextResponse)
async def get_report(plugin: str, name: str, session: db.SessionDep):
    device_name = get_device_name(plugin, name)
    return rm.get_report(session, plugin, device_name)


@router.delete("/plugins/{plugin}/devices/{name}/delete")
async def delete_device(plugin: str, name: str, session: db.SessionDep):
    device_name = get_device_name(plugin, name)
    db.remove_device(device_name)
    return rm.delete_report(session, plugin, device_name)
