import argparse
import os
from pathlib import Path

import uvicorn


def get_args():
    parser = argparse.ArgumentParser(
        prog="mqtt-rest-server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="MQTT REST Server\nSee help: https://www.github.com/rahulsrma26/mqtt-rest",
    )
    parser.add_argument(
        "-e",
        "--env-file",
        type=Path,
        default=os.path.join(os.path.curdir, "dev.env"),
        help="Path to the environment file",
    )
    parser.add_argument(
        "-i",
        "--server-ip",
        type=str,
        default="",
        help="Host to bind the server",
    )
    parser.add_argument(
        "-p",
        "--server-port",
        type=int,
        default=0,
        help="Port to bind the server",
    )
    parser.add_argument(
        "-l",
        "--server-log-level",
        type=str,
        default="",
        help="Log level for the server",
    )
    parser.add_argument(
        "-bi",
        "--broker-ip",
        type=str,
        default="",
        help="IP of the MQTT Broker",
    )
    parser.add_argument(
        "-bp",
        "--broker-port",
        type=int,
        default=0,
        help="Port of the MQTT Broker",
    )
    parser.add_argument(
        "-mu",
        "--mqtt-user",
        type=str,
        default="",
        help="Username for the MQTT Broker",
    )
    parser.add_argument(
        "-mp",
        "--mqtt-password",
        type=str,
        default="",
        help="Password for the MQTT Broker",
    )
    parser.add_argument(
        "-ml",
        "--mqtt-log",
        action="store_true",
        default=False,
        help="Enable logger for the MQTT Broker",
    )
    return parser.parse_args()


def main():
    args = get_args()
    if args.env_file and os.path.exists(args.env_file):
        print(f"Loading environment variables from {args.env_file}")
        with open(args.env_file) as f:
            for line in f:
                key, value = line.strip().split("=")
                os.environ[key] = value
    for key, value in vars(args).items():
        if value:
            os.environ[key.upper()] = str(value)

    app = "mqtt_rest.server:app"
    kwargs = {
        "host": "0.0.0.0",
        "port": int(os.getenv("SERVER_PORT", 9000)),
        "log_level": os.getenv("SERVER_LOG_LEVEL", "info"),
    }
    uvicorn.run(app, **kwargs)


if __name__ == "__main__":
    main()
