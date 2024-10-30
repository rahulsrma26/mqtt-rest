import re
from typing import Dict, Tuple

from mqtt_rest.plugins import simple_plugin as sp


def parse_group(text: str) -> Tuple[str, float]:
    device = data_units_written = None
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        if key.strip() == "device":
            device = value.strip()
        elif key.strip() == "total bytes written":
            data_units_written = round(float(re.search(r"(\d+)", value).group(1)) / (10**9), 3)
    return device, data_units_written


def parser(output: str) -> Dict[str, sp.SensorValue]:
    sensors = {}
    for group in re.split(r"\n-+\n", output):
        name, value = parse_group(group.lower())
        if name and value:
            sensors[f"{name}"] = sp.SensorValue(
                value=value,
                unit="GB",
            )
    return sensors


smartwrt = sp.SimplePlugin(
    name="smartwrt",
    install=sp.Installer(
        dependencies=[
            sp.Command(
                command="smartctl",
                install_func=sp.BashFunction(
                    body=r"""
                        apt install -y smartmontools && systemctl enable smartd
                        """
                ),
            ),
            sp.Command(
                command="smartwrt",
                install_func=sp.BashFunction(
                    body=r"""
                        wget -qLO /usr/local/sbin/smartwrt https://github.com/rahulsrma26/scripts/raw/main/manage/debian/smartwrt.sh
                        chmod +x /usr/local/sbin/smartwrt
                        """
                ),
            ),
        ],
        description="""
            This plugin uses the "smartctl" command to get the amount of data written to the disk.
            """,
    ),
    manager=sp.SingleJob(
        job_func=sp.BashFunction(
            body=r"""
                /usr/local/sbin/smartwrt
                """,
            name="run_job",
        ),
        freq2cron_func=sp.JOB_FREQUENCY_HOUR_DAY,
        need_root=True,
    ),
    parser=parser,
)
