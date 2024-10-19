from mqtt_rest.plugins.sensors.routes import router as sensors
from mqtt_rest.plugins.smartwrt.routes import router as smartwrt

all_plugins = {
    "sensors": sensors,
    "smartwrt": smartwrt,
}
