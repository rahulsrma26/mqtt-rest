import re
from typing import Dict

from mqtt_rest.plugins import simple_plugin as sp


def parser(output: str) -> Dict[str, sp.SensorValue]:
    groups = output.split("\n\n")
    sensors = {}
    for group in groups:
        name = group.split("\n")[0]
        for line in group.split("\n"):
            match = re.match(r"^(.*?):\s+\+([0-9.]+)°C", line)
            if match:
                sensor, value = match.groups()
                sensors[f"{name} {sensor}"] = sp.SensorValue(
                    value=float(value),
                    unit="°C",
                )
    return sensors


sensors = sp.SimplePlugin(
    name="sensors",
    install=sp.Installer(
        dependencies=[
            sp.Command(
                command="sensors",
                install_func=sp.BashFunction(
                    body=r"""
                        apt install -y lm-sensors
                        """
                ),
            )
        ],
        description="""
            This plugin uses the "sensors" command to get the temperature of the CPU and other sensors.
            """,
    ),
    manager=sp.SingleJob(
        job_func=sp.BashFunction(
            body=r"""
                sensors
                """,
            name="run_job",
        ),
        freq2cron_func=sp.JOB_FREQUENCY_MINUTE_HOUR_DAY,
    ),
    parser=parser,
)
