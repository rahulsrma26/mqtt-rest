"""
Parse the output of the sensors command
and return a dictionary of the sensor values
"""

import re
from typing import Dict


def parse_report(output: str) -> Dict[str, float]:
    groups = output.split("\n\n")
    sensors = {}
    for group in groups:
        name = group.split("\n")[0]
        for line in group.split("\n"):
            match = re.match(r"^(.*?):\s+\+([0-9.]+)°C", line)
            if match:
                sensor, value = match.groups()
                sensors[f"{name} {sensor}"] = float(value)
    return sensors
