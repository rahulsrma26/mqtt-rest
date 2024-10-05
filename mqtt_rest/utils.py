import base64
import hashlib
import socket


def get_internal_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    return ip


def get_unique_id(text: str) -> str:
    return "_" + (
        base64.b64encode(hashlib.md5(text.encode()).digest())
        .decode()
        .replace("=", "")
        .replace("/", "_")
        .replace("+", "")
    )
