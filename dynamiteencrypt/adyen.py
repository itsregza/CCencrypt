import json
import os
from datetime import datetime, timezone

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from dynamiteencrypt.encoding import b64url, hex_to_bytes, pack_bit_length


def now_iso():
    dt = datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{int(dt.microsecond / 1000):03d}Z"


class AdyenEncryptor:
    def __init__(self, site_key):
        self.site_key = site_key
        self.key_object = None

    def generate_key(self):
        parts = self.site_key.split("|")
        if len(parts) != 2:
            raise ValueError("malformed public key: incorrect split parts")
        exp_bytes = hex_to_bytes(parts[0])
        mod_bytes = hex_to_bytes(parts[1])
        self.key_object = {
            "kty": "RSA",
            "kid": "asf-key",
            "e": b64url(exp_bytes),
            "n": b64url(mod_bytes),
            "alg": "RSA-OAEP",
        }
        return self.key_object

    def public_key(self):
        if not self.key_object:
            self.generate_key()
        e = int.from_bytes(hex_to_bytes(self.site_key.split("|")[0]), "big")
        n = int.from_bytes(hex_to_bytes(self.site_key.split("|")[1]), "big")
        return rsa.RSAPublicNumbers(e, n).public_key(default_backend())

    def encrypt_data(self, plain_text):
        if not self.key_object:
            self.generate_key()

        cek = os.urandom(64)
        encrypted_key = self.public_key().encrypt(
            cek,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA1()),
                algorithm=hashes.SHA1(),
                label=None,
            ),
        )

        protected_header = {"alg": "RSA-OAEP", "enc": "A256CBC-HS512", "version": "1"}
        protected_b64 = b64url(json.dumps(protected_header, separators=(",", ":")))
        protected_bytes = protected_b64.encode("utf-8")

        iv = os.urandom(16)
        plaintext = json.dumps(plain_text, separators=(",", ":")).encode("utf-8")

        aes_key = cek[32:]
        hmac_key = cek[:32]

        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        pad_len = 16 - (len(plaintext) % 16)
        padded = plaintext + bytes([pad_len]) * pad_len
        ciphertext = encryptor.update(padded) + encryptor.finalize()

        length_bytes = pack_bit_length(len(protected_bytes))
        mac = hmac.HMAC(hmac_key, hashes.SHA512(), backend=default_backend())
        mac.update(protected_bytes + iv + ciphertext + length_bytes)
        tag = mac.finalize()[:32]

        return ".".join(
            [
                protected_b64,
                b64url(encrypted_key),
                b64url(iv),
                b64url(ciphertext),
                b64url(tag),
            ]
        )


def dynamiteadyen(
    adyen_key,
    card,
    month,
    year,
    cvc,
    stripe_key=None,
    domain=None,
):
    if not card or not month or not year or not cvc:
        raise ValueError("missing card details")
    if not adyen_key:
        raise ValueError("missing adyen key")
    if not stripe_key:
        stripe_key = "live_2WKDYLJCMBFC5CFHBXY2CHZF4MUUJ7QU"
    if not domain:
        domain = "https://www.mytheresa.com"

    domain_b64 = b64url(domain.encode("utf-8"))
    referrer = (
        f"https://checkoutshopper-live.adyen.com/checkoutshopper/securedfields/"
        f"{stripe_key}/4.5.0/securedFields.html?type=card&d={domain_b64}"
    )

    card_clean = str(card).strip().replace(" ", "").replace("-", "")
    card_number = " ".join(card_clean[i : i + 4] for i in range(0, len(card_clean), 4))

    ts = now_iso()
    card_detail = {
        "encryptedCardNumber": {
            "number": card_number,
            "generationtime": ts,
            "numberBind": "1",
            "activate": "3",
            "referrer": referrer,
            "numberFieldFocusCount": "3",
            "numberFieldLog": "fo@44070,cl@44071,KN@44082,fo@44324,cl@44325,cl@44333,KN@44346,KN@44347,KN@44348,KN@44350,KN@44351,KN@44353,KN@44354,KN@44355,KN@44356,KN@44358,fo@44431,cl@44432,KN@44434,KN@44436,KN@44438,KN@44440,KN@44440",
            "numberFieldClickCount": "4",
            "numberFieldKeyCount": "16",
        },
        "encryptedExpiryMonth": {"expiryMonth": str(month), "generationtime": ts},
        "encryptedExpiryYear": {"expiryYear": str(year), "generationtime": ts},
        "encryptedSecurityCode": {
            "cvc": str(cvc),
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

    enc = AdyenEncryptor(adyen_key)
    enc.generate_key()
    for key in list(card_detail.keys()):
        card_detail[key] = enc.encrypt_data(card_detail[key])
    return card_detail
