import base64
import json
import os

from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESCCM

CSE_VERSIONS = ("0_1_18", "0_1_22", "0_1_23", "0_1_24", "0_1_25")


def normalize_cse_version(version):
    v = str(version).strip().lower().replace("adyenjs_", "").replace(".", "_")
    if v.isdigit():
        v = f"0_1_{v}"
    if v not in CSE_VERSIONS:
        raise ValueError(f"unsupported adyen cse version: {version!r}")
    return v


def cse_extra_fields(version):
    # Fields the adyen-encrypt JS lib appends to every payload for this version.
    if version == "0_1_18":
        return {"initializeCount": "1", "dfValue": ""}
    if version == "0_1_25":
        return {"initializeCount": "1", "sjclStrength": "10"}
    return {"initializeCount": "1", "sjclStrength": "10", "dfValue": ""}


def cse_encrypt(data, public_key, version="0_1_25"):
    version = normalize_cse_version(version)
    payload = dict(data)
    payload.update(cse_extra_fields(version))
    plaintext = json.dumps(payload, separators=(",", ":")).encode("utf-8")

    aes_key = os.urandom(32)
    iv = os.urandom(12)
    cipher = AESCCM(aes_key, tag_length=8).encrypt(iv, plaintext, None)
    wrapped_key = public_key.encrypt(aes_key, padding.PKCS1v15())

    return "".join([
        f"adyenjs_{version}$",
        base64.b64encode(wrapped_key).decode("ascii"),
        "$",
        base64.b64encode(iv + cipher).decode("ascii"),
    ])
