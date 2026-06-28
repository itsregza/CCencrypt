import json
import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from dynamiteencrypt.encoding import b64url, b64url_decode, jwt_payload


CardTypes = {
    "Visa": "001",
    "MasterCard": "002",
    "AmericanExpress": "003",
    "Discover": "004",
    "Diners": "005",
    "JCB": "007",
    "Maestro": "042",
    "ChinaUnionPay": "062",
}


def card_type(number):
    n = str(number).strip().replace(" ", "").replace("-", "")
    if n.startswith("5"):
        return CardTypes["MasterCard"]
    if n.startswith("34") or n.startswith("37"):
        return CardTypes["AmericanExpress"]
    return CardTypes["Visa"]


def jwk_rsa_key(jwk):
    e = int.from_bytes(b64url_decode(jwk["e"]), "big")
    n = int.from_bytes(b64url_decode(jwk["n"]), "big")
    return rsa.RSAPublicNumbers(e, n).public_key(default_backend())


def dynamitecybersource(card, month, year, cvv, context, index=0):
    key_id = jwt_payload(context)
    jwk = key_id["flx"]["jwk"]
    header = {
        "kid": jwk["kid"],
        "alg": "RSA-OAEP",
        "enc": "A256GCM",
    }
    payload = {
        "data": {
            "number": str(card).strip().replace(" ", "").replace("-", ""),
            "securityCode": str(cvv),
            "expirationMonth": str(month),
            "expirationYear": str(year),
            "type": card_type(card),
        },
        "context": context,
        "index": index,
    }

    iv = os.urandom(12)
    aes_key = AESGCM.generate_key(bit_length=256)
    header_b64 = b64url(json.dumps(header, separators=(",", ":")))
    aad = header_b64.encode("utf-8")
    plaintext = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    encrypted = AESGCM(aes_key).encrypt(iv, plaintext, aad)

    tag_len = 16
    body = encrypted[:-tag_len]
    tag = encrypted[-tag_len:]

    wrapped = jwk_rsa_key(jwk).encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA1()),
            algorithm=hashes.SHA1(),
            label=None,
        ),
    )

    return ".".join(
        [
            header_b64,
            b64url(wrapped),
            b64url(iv),
            b64url(body),
            b64url(tag),
        ]
    )
