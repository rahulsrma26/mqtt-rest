import uvicorn
from mqtt_rest.server import app


def main():
    uvicorn.run(app, host="0.0.0.0", port=9000, log_level="debug")


if __name__ == "__main__":
    main()
