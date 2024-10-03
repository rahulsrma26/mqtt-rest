from contextlib import asynccontextmanager
from typing import Dict, Union
from threading import Lock
from fastapi import FastAPI, HTTPException, Body
from mqtt_rest import db


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.add_source_device()
    yield
    print("Cleaning up devices")
    for device in db.all_devices.values():
        device.bulk_remove()
    db.remove_source_device()


app = FastAPI(lifespan=lifespan)
lock = Lock()

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
