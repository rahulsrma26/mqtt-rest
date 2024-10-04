import os
import uvicorn
from mqtt_rest.server import app


def main():
    log_level = os.environ.get("SERVER_LOG_LEVEL", "info")
    uvicorn.run(app, host="0.0.0.0", port=9000, log_level=log_level)


if __name__ == "__main__":
    main()
