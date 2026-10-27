import uuid

import requests

from ccencrypt.helpers.card import clean_card, expiry, proxies

STRIPE_PM_URL = "https://api.stripe.com/v1/payment_methods"
STRIPE_JS = "stripe.js/e2a5fc9c3e; stripe-js-v3/e2a5fc9c3e; card-element"


def ccstripe(key, card, month, year, cvc, name="", account=None, proxy=None, timeout=30):
    month, year = expiry(month, year)
    data = {
        "type": "card",
        "card[number]": clean_card(card),
        "card[cvc]": str(cvc).strip(),
        "card[exp_month]": month,
        "card[exp_year]": year[-2:],
        "payment_user_agent": STRIPE_JS,
        "guid": str(uuid.uuid4()),
        "muid": str(uuid.uuid4()),
        "sid": str(uuid.uuid4()),
        "key": key,
    }
    if name:
        data["billing_details[name]"] = name
    if account:
        data["_stripe_account"] = account

    resp = requests.post(
        STRIPE_PM_URL,
        headers={
            "accept": "application/json",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://js.stripe.com",
            "referer": "https://js.stripe.com/",
        },
        data=data,
        proxies=proxies(proxy),
        timeout=timeout,
    )
    body = resp.json() if resp.text else {}
    pm = body.get("id", "")
    if resp.status_code != 200 or not pm.startswith("pm_"):
        err = body.get("error") or {}
        raise RuntimeError(f"stripe failed: {resp.status_code} {err.get('message') or resp.text[:300]}")
    return pm
