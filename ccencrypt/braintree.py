import base64
import json
import uuid

import requests

BRAINTREE_GQL_URL = "https://payments.braintree-api.com/graphql"

TOKENIZE_QUERY = (
    "mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) { "
    "tokenizeCreditCard(input: $input) { token creditCard { bin brandCode last4 } } }"
)


def fingerprint(client_token):
    try:
        data = json.loads(base64.b64decode(client_token))
    except Exception:
        return client_token
    return data["authorizationFingerprint"]


def ccbraintree(client_token, card, month, year, cvv, name="", proxy=None, timeout=30):
    payload = {
        "clientSdkMetadata": {
            "source": "client",
            "integration": "custom",
            "sessionId": str(uuid.uuid4()),
        },
        "query": TOKENIZE_QUERY,
        "variables": {
            "input": {
                "creditCard": {
                    "number": str(card).strip().replace(" ", "").replace("-", ""),
                    "expirationMonth": str(month).strip().zfill(2),
                    "expirationYear": str(year).strip(),
                    "cvv": str(cvv).strip(),
                    "cardholderName": name,
                },
                "options": {"validate": False},
            }
        },
        "operationName": "TokenizeCreditCard",
    }

    resp = requests.post(
        BRAINTREE_GQL_URL,
        headers={
            "authorization": f"Bearer {fingerprint(client_token)}",
            "braintree-version": "2018-05-10",
            "content-type": "application/json",
            "origin": "https://assets.braintreegateway.com",
            "referer": "https://assets.braintreegateway.com/",
        },
        json=payload,
        proxies={"http": proxy, "https": proxy} if proxy else None,
        timeout=timeout,
    )
    body = resp.json() if resp.text else {}
    token = ((body.get("data") or {}).get("tokenizeCreditCard") or {}).get("token")
    if resp.status_code != 200 or not token:
        raise RuntimeError(f"braintree failed: {resp.status_code} {resp.text[:300]}")
    return token
