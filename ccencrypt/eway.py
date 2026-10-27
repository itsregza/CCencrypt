import base64

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from ccencrypt.helpers.card import clean_card


def modulus_from_key_blob(key_blob):
    try:
        mod_bytes = base64.b64decode(key_blob)
    except Exception as exc:
        raise ValueError("invalid encrypt key") from exc
    n = int.from_bytes(mod_bytes, "big")
    return rsa.RSAPublicNumbers(65537, n).public_key(default_backend())


def cceway(encrypt_key, value):
    if not encrypt_key:
        raise ValueError("missing encrypt key")
    if value is None or str(value).strip() == "":
        raise ValueError("missing value")

    pub = modulus_from_key_blob(str(encrypt_key).strip())
    ciphertext = pub.encrypt(str(value).encode("utf-8"), padding.PKCS1v15())
    return "eCrypted:" + base64.b64encode(ciphertext).decode("ascii")


def cceway_card(encrypt_key, card, cvv):
    pan = clean_card(card)
    code = str(cvv).strip()
    return {
        "EWAY_CARDNUMBER": cceway(encrypt_key, pan),
        "EWAY_CARDCVN": cceway(encrypt_key, code),
    }
