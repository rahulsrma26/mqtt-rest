"""
Parse the output of the command
and return a dictionary of the sensor values
"""

import re
from typing import Dict, Tuple


def parse_group(text: str) -> Tuple[str, float]:
    device = data_units_written = None
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        if key.strip() == "device":
            device = value.strip()
        elif key.strip() == "total bytes written":
            data_units_written = round(float(re.search(r"(\d+)", value).group(1)) / (1024**3), 3)
    return device, data_units_written


def parse_report(output: str) -> Dict[str, float]:
    sensors = {}
    for group in re.split(r"\n-+\n", output):
        name, value = parse_group(group.lower())
        if name and value:
            sensors[f"{name}"] = value
    return sensors
