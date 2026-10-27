import requests

from ccencrypt.helpers.card import clean_card, proxies

PAYDOCK_TOKENS_URL = "https://api.paydock.com/v1/payment_sources/tokens"


def ccpaydock(public_key, card, month, year, cvv, name, gateway_id="", proxy=None, timeout=30):
    payload = {
        "type": "card",
        "card_name": name,
        "card_number": clean_card(card),
        "expire_month": str(month).strip().zfill(2)[-2:],
        "expire_year": str(year).strip()[-2:],
        "card_ccv": str(cvv).strip(),
        "gateway_id": gateway_id,
        "store_ccv": True,
        "meta": {},
    }

    resp = requests.post(
        PAYDOCK_TOKENS_URL,
        headers={
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "origin": "https://widget.paydock.com",
            "referer": "https://widget.paydock.com/",
            "x-sdk-type": "client",
            "x-sdk-version": "v1.131.0",
            "x-user-public-key": public_key,
        },
        json=payload,
        proxies=proxies(proxy),
        timeout=timeout,
    )
    body = resp.json() if resp.text else {}
    token = (body.get("resource") or {}).get("data")
    if resp.status_code != 201 or not token:
        raise RuntimeError(f"paydock failed: {resp.status_code} {resp.text[:300]}")
    return token
