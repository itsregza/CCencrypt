import requests

from ccencrypt.helpers.card import expiry, proxies, spaced_card

SHOPIFY_PCI_URL = "https://checkout.pci.shopifyinc.com/sessions"


def ccshopify(domain, card, month, year, cvv, name, proxy=None, timeout=30):
    month, year = expiry(month, year)
    payload = {
        "credit_card": {
            "number": spaced_card(card),
            "month": int(month),
            "year": int(year),
            "verification_value": str(cvv).strip(),
            "start_month": None,
            "start_year": None,
            "issue_number": "",
            "name": name,
        },
        "payment_session_scope": domain.replace("https://", "").replace("www.", "").strip("/"),
    }

    resp = requests.post(
        SHOPIFY_PCI_URL,
        headers={
            "accept": "application/json",
            "content-type": "application/json",
            "origin": "https://checkout.pci.shopifyinc.com",
            "referer": "https://checkout.pci.shopifyinc.com/",
        },
        json=payload,
        proxies=proxies(proxy),
        timeout=timeout,
    )
    body = resp.json() if resp.text else {}
    session_id = body.get("id")
    if resp.status_code != 200 or not session_id:
        raise RuntimeError(f"shopify failed: {resp.status_code} {resp.text[:300]}")
    return session_id
