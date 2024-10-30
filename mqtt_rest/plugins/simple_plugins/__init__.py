from mqtt_rest.plugins.simple_plugins.sensors import sensors
from mqtt_rest.plugins.simple_plugins.smartwrt import smartwrt

PLUGINS = {
    "sensors": sensors,
    "smartwrt": smartwrt,
}
