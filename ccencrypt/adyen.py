import base64
import json
import os
from datetime import datetime, timezone

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from ccencrypt.adyen_cse import cse_encrypt
from ccencrypt.helpers.card import clean_card, expiry
from ccencrypt.helpers.encoding import b64url, hex_to_bytes, pack_bit_length

OAEP = padding.OAEP(
    mgf=padding.MGF1(algorithm=hashes.SHA1()),
    algorithm=hashes.SHA1(),
    label=None,
)


def utc_stamp():
    dt = datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{int(dt.microsecond / 1000):03d}Z"


def parse_public_key(encrypt_key):
    parts = encrypt_key.split("|", 1)
    if len(parts) != 2:
        raise ValueError("malformed encrypt key")
    e = int.from_bytes(hex_to_bytes(parts[0]), "big")
    n = int.from_bytes(hex_to_bytes(parts[1]), "big")
    return rsa.RSAPublicNumbers(e, n).public_key(default_backend())


def jwe_encrypt(payload, public_key):
    dek = os.urandom(64)
    wrapped_key = public_key.encrypt(dek, OAEP)

    header_json = json.dumps(
        {"alg": "RSA-OAEP", "enc": "A256CBC-HS512", "version": "1"},
        separators=(",", ":"),
    )
    header_b64 = b64url(header_json.encode("utf-8"))
    header_raw = header_b64.encode("utf-8")

    iv = os.urandom(16)
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    pad = 16 - (len(body) % 16)
    body = body + bytes([pad]) * pad

    enc = Cipher(algorithms.AES(dek[32:]), modes.CBC(iv), backend=default_backend()).encryptor()
    ciphertext = enc.update(body) + enc.finalize()

    mac = hmac.HMAC(dek[:32], hashes.SHA512(), backend=default_backend())
    mac.update(header_raw + iv + ciphertext + pack_bit_length(len(header_raw)))
    auth_tag = mac.finalize()[:32]

    return ".".join([header_b64, b64url(wrapped_key), b64url(iv), b64url(ciphertext), b64url(auth_tag)])


def secured_fields_referrer(client_key, domain):
    d = base64.b64encode(domain.encode("utf-8")).decode("ascii")
    return (
        "https://checkoutshopper-live.adyen.com/checkoutshopper/securedfields/"
        f"{client_key}/4.5.0/securedFields.html?type=card&d={d}"
    )


def format_pan(card):
    digits = clean_card(card)
    return " ".join(digits[i : i + 4] for i in range(0, len(digits), 4))


def build_card_payloads(card, month, year, cvc, referrer, ts):
    pan = format_pan(card)
    month, year = expiry(month, year)
    cvc = str(cvc)
    return {
        "encryptedCardNumber": {
            "number": pan,
            "generationtime": ts,
            "numberBind": "1",
            "activate": "3",
            "referrer": referrer,
            "numberFieldFocusCount": "3",
            "numberFieldLog": "fo@44070,cl@44071,KN@44082,fo@44324,cl@44325,cl@44333,KN@44346,KN@44347,KN@44348,KN@44350,KN@44351,KN@44353,KN@44354,KN@44355,KN@44356,KN@44358,fo@44431,cl@44432,KN@44434,KN@44436,KN@44438,KN@44440,KN@44440",
            "numberFieldClickCount": "4",
            "numberFieldKeyCount": "16",
        },
        "encryptedExpiryMonth": {"expiryMonth": month, "generationtime": ts},
        "encryptedExpiryYear": {"expiryYear": year, "generationtime": ts},
        "encryptedSecurityCode": {
            "cvc": cvc,
            "generationtime": ts,
            "cvcBind": "1",
            "activate": "4",
            "referrer": referrer,
            "cvcFieldFocusCount": "4",
            "cvcFieldLog": "fo@122,cl@123,KN@136,KN@138,KN@140,fo@11204,cl@11205,ch@11221,bl@11221,fo@33384,bl@33384,fo@50318,cl@50319,cl@50321,KN@50334,KN@50336,KN@50336",
            "cvcFieldClickCount": "4",
            "cvcFieldKeyCount": "6",
            "cvcFieldChangeCount": "1",
            "cvcFieldBlurCount": "2",
            "deactivate": "2",
        },
    }


def ccadyen(
    encrypt_key,
    card,
    month,
    year,
    cvc,
    client_key=None,
    domain=None,
    version="4.5.0",
):
    if not card or not month or not year or not cvc:
        raise ValueError("missing card details")
    if not encrypt_key:
        raise ValueError("missing encrypt key")
    if str(version).strip() != "4.5.0":
        return ccadyen_cse(encrypt_key, card, month, year, cvc, version=version)
    if not client_key:
        client_key = "live_SQV7J3WVMNFK3HU33BTUNF5AH4E2L2ZN"
    if not domain:
        domain = "https://minisoshop.co.uk"

    rsa_key = parse_public_key(encrypt_key)
    referrer = secured_fields_referrer(client_key, domain)
    ts = utc_stamp()
    fields = build_card_payloads(card, month, year, cvc, referrer, ts)

    return {name: jwe_encrypt(data, rsa_key) for name, data in fields.items()}


def ccadyen_cse(encrypt_key, card, month, year, cvc, version="0_1_25"):
    if not card or not month or not year or not cvc:
        raise ValueError("missing card details")
    if not encrypt_key:
        raise ValueError("missing encrypt key")

    rsa_key = parse_public_key(encrypt_key)
    ts = utc_stamp()
    month, year = expiry(month, year)
    fields = {
        "encryptedCardNumber": {"number": format_pan(card), "generationtime": ts},
        "encryptedExpiryMonth": {"expiryMonth": month, "generationtime": ts},
        "encryptedExpiryYear": {"expiryYear": year, "generationtime": ts},
        "encryptedSecurityCode": {"cvc": str(cvc), "generationtime": ts},
    }
    return {name: cse_encrypt(data, rsa_key, version) for name, data in fields.items()}
