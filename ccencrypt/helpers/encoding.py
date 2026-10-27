import base64
import json


def b64url(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return base64.b64encode(data).decode("ascii").rstrip("=").replace("+", "-").replace("/", "_")


def hex_to_bytes(hex_str):
    if not hex_str:
        return b""
    if len(hex_str) % 2 == 1:
        hex_str = "0" + hex_str
    return bytes.fromhex(hex_str)


def b64url_decode(s):
    s = s.replace("-", "+").replace("_", "/")
    pad = "=" * ((4 - len(s) % 4) % 4)
    return base64.b64decode(s + pad)


def jwt_payload(token):
    part = token.split(".")[1]
    return json.loads(b64url_decode(part))


def pack_bit_length(length_bytes):
    bits = length_bytes * 8
    hi = bits // (2**32)
    lo = bits % (2**32)
    return hi.to_bytes(4, "big") + lo.to_bytes(4, "big")
