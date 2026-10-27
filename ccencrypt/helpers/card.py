def clean_card(card):
    return str(card).strip().replace(" ", "").replace("-", "")


def spaced_card(card):
    n = clean_card(card)
    if len(n) == 15:
        return f"{n[:4]} {n[4:10]} {n[10:]}"
    return " ".join(n[i : i + 4] for i in range(0, len(n), 4))


def proxies(proxy):
    return {"http": proxy, "https": proxy} if proxy else None
