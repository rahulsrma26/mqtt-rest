import os
import argparse
import uvicorn


def get_args():
    parser = argparse.ArgumentParser(
        prog="mqtt-rest-server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="MQTT REST Server\nSee help: https://www.github.com/rahulsrma26/mqtt-rest",
    )
    parser.add_argument(
        "-i",
        "--server-ip",
        type=str,
        default=os.environ.get("SERVER_IP", ""),
        help="Host to bind the server",
    )
    parser.add_argument(
        "-p",
        "--server-port",
        type=int,
        default=os.environ.get("SERVER_PORT", 9000),
        help="Port to bind the server",
    )
    parser.add_argument(
        "-l",
        "--server-log-level",
        type=str,
        default=os.environ.get("SERVER_LOG_LEVEL", "info"),
        help="Log level for the server",
    )
    parser.add_argument(
        "-bi",
        "--broker-ip",
        type=str,
        default=os.environ.get("BROKER_IP", ""),
        help="IP of the MQTT Broker",
    )
    parser.add_argument(
        "-bp",
        "--broker-port",
        type=int,
        default=os.environ.get("BROKER_PORT", 1883),
        help="Port of the MQTT Broker",
    )
    parser.add_argument(
        "-mu",
        "--mqtt-user",
        type=str,
        default=os.environ.get("MQTT_USER", ""),
        help="Username for the MQTT Broker",
    )
    parser.add_argument(
        "-mp",
        "--mqtt-password",
        type=str,
        default=os.environ.get("MQTT_PASSWORD", ""),
        help="Password for the MQTT Broker",
    )
    parser.add_argument(
        "-ml",
        "--mqtt-log",
        action="store_true",
        default=os.environ.get("MQTT_LOG", False),
        help="Enable logger for the MQTT Broker",
    )
    return parser.parse_args()


def main():
    args = get_args()
    for key, value in vars(args).items():
        os.environ[key.upper()] = str(value)

    app = "mqtt_rest.server:app"
    uvicorn.run(app, host=args.server_ip, port=args.server_port, log_level=args.server_log_level)


if __name__ == "__main__":
    main()
