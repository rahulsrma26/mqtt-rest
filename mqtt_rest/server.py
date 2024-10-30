from contextlib import asynccontextmanager
from threading import Lock
from typing import Dict, Union

from fastapi import Body, FastAPI, HTTPException

from mqtt_rest import db
from mqtt_rest.configs import SERVER_CONFIG as CONFIG
from mqtt_rest.mqtt import MQTTBroker
from mqtt_rest.plugins.routes import plugin_names
from mqtt_rest.plugins.routes import router as plugins_router

mqttclient = MQTTBroker()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Visit the API at", CONFIG.url + "/docs", flush=True)
    if not mqttclient.connect():
        raise Exception("Failed to connect to MQTT Broker")
    db.create_db_and_tables()
    db.add_source_device()
    yield
    print("Cleaning up devices", flush=True)
    for device in db.all_devices.values():
        device.bulk_remove()
    db.remove_source_device()
    mqttclient.disconnect()


app = FastAPI(lifespan=lifespan)
lock = Lock()
app.include_router(plugins_router, prefix="/api/v1")

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
    return plugin_names
