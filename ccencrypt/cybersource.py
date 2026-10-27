import json
import os
import urllib.parse

import requests

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from ccencrypt.helpers.card import clean_card, expiry, proxies
from ccencrypt.helpers.encoding import b64url, b64url_decode, jwt_payload

FLEX_TOKENS_URL = "https://flex.cybersource.com/flex/v2/tokens"


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
    n = clean_card(number)
    if n.startswith("5"):
        return CardTypes["MasterCard"]
    if n.startswith("34") or n.startswith("37"):
        return CardTypes["AmericanExpress"]
    return CardTypes["Visa"]


def jwk_rsa_key(jwk):
    e = int.from_bytes(b64url_decode(jwk["e"]), "big")
    n = int.from_bytes(b64url_decode(jwk["n"]), "big")
    return rsa.RSAPublicNumbers(e, n).public_key(default_backend())


def cccybersource(card, month, year, cvv, context, index=0):
    key_id = jwt_payload(context)
    jwk = key_id["flx"]["jwk"]
    header = {
        "kid": jwk["kid"],
        "alg": "RSA-OAEP",
        "enc": "A256GCM",
    }
    month, year = expiry(month, year)
    payload = {
        "data": {
            "number": clean_card(card),
            "securityCode": str(cvv),
            "expirationMonth": month,
            "expirationYear": year,
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


def microform_referer(context):
    kid = jwt_payload(context)["flx"]["jwk"]["kid"]
    q = urllib.parse.quote(kid, safe="")
    return f"https://flex.cybersource.com/microform/bundle/v2.9.0/iframe.html?keyId={q}"


def cccybersource_token(
    card,
    month,
    year,
    cvv,
    context,
    origin=None,
    referer=None,
    user_agent=None,
    microform=False,
    index=0,
    proxy=None,
    timeout=30,
):
    encrypted = cccybersource(card, month, year, cvv, context, index=index)

    if microform:
        headers = {
            "content-type": "application/jwt; charset=UTF-8",
            "origin": "https://flex.cybersource.com",
            "referer": referer or microform_referer(context),
        }
    else:
        if not origin:
            raise ValueError("origin required unless microform=True")
        site = origin.rstrip("/")
        headers = {
            "content-type": "application/jwt",
            "origin": site,
            "referer": referer or f"{site}/",
        }

    if user_agent:
        headers["user-agent"] = user_agent

    resp = requests.post(
        FLEX_TOKENS_URL,
        headers=headers,
        data=str(encrypted).strip(),
        proxies=proxies(proxy),
        timeout=timeout,
    )
    if resp.status_code != 201:
        raise RuntimeError(f"flex /tokens failed: {resp.status_code} {(resp.text or '')[:300]}")
    token = (resp.text or "").strip()
    if not token:
        raise RuntimeError("flex /tokens returned empty body")
    return token
