import requests

SHOPIFY_PCI_URL = "https://checkout.pci.shopifyinc.com/sessions"


def spaced(card):
    n = str(card).strip().replace(" ", "").replace("-", "")
    if len(n) == 15:
        return f"{n[:4]} {n[4:10]} {n[10:]}"
    return " ".join(n[i : i + 4] for i in range(0, len(n), 4))


def ccshopify(domain, card, month, year, cvv, name, proxy=None, timeout=30):
    year = str(year).strip()
    if len(year) == 2:
        year = "20" + year
    payload = {
        "credit_card": {
            "number": spaced(card),
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
        proxies={"http": proxy, "https": proxy} if proxy else None,
        timeout=timeout,
    )
    body = resp.json() if resp.text else {}
    session_id = body.get("id")
    if resp.status_code != 200 or not session_id:
        raise RuntimeError(f"shopify failed: {resp.status_code} {resp.text[:300]}")
    return session_id
