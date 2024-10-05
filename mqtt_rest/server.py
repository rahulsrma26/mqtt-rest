from contextlib import asynccontextmanager
from typing import Dict, Union
from threading import Lock
from fastapi import FastAPI, HTTPException, Body
from mqtt_rest import db
from mqtt_rest.configs import SERVER_CONFIG as CONFIG
from mqtt_rest.plugins import all_plugins
from mqtt_rest.mqtt import MQTTBroker

mqttclient = MQTTBroker()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Visit the API at", CONFIG.url + "/docs")
    if not mqttclient.connect():
        raise Exception("Failed to connect to MQTT Broker")
    db.add_source_device()
    yield
    print("Cleaning up devices")
    for device in db.all_devices.values():
        device.bulk_remove()
    db.remove_source_device()
    mqttclient.disconnect()


app = FastAPI(lifespan=lifespan)
lock = Lock()
for plugin in all_plugins.values():
    app.include_router(plugin, prefix="/api/v1/plugins")

# origins = "*"
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


SensorValueType = Union[bool, int, float, str]
BulkSensorValuesType = Dict[str, SensorValueType]


@app.get("/api/v1/devices")
async def get_all_devices():
    return list(db.all_devices.keys())


@app.get("/api/v1/devices/{device_name}")
async def get_device(device_name: str):
    device = db.get_device(device_name, create=False)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device.get_config()


@app.put("/api/v1/devices/{device_name}")
async def put_device(device_name: str, values: BulkSensorValuesType = Body(...)):
    device = db.get_device(device_name)
    return device.bulk_update(values)


@app.delete("/api/v1/devices/{device_name}")
async def delete_device(device_name: str):
    db.remove_device(device_name)


@app.put("/api/v1/devices/{device_name}/sensors/{sensor_name}")
async def put_sensor(
    device_name: str, sensor_name: str, value: SensorValueType = Body(..., embed=True)
):
    device = db.get_device(device_name)
    return device.update(sensor_name, value)


@app.delete("/api/v1/devices/{device_name}/sensors/{sensor_name}")
async def delete_sensor(device_name: str, sensor_name: str):
    device = db.get_device(device_name, create=False)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device.remove_sensor(sensor_name)


@app.get("/api/v1/plugins")
async def get_plugins():
    return list(all_plugins.keys())
