<p align="center">
  <img src="https://raw.githubusercontent.com/itsregza/CCencrypt/main/assets/banner.svg" alt="CCencrypt" width="520">
</p>

<p align="center">Card encryption and tokenisation for Python.</p>
<p align="center">
  <a href="https://pypi.org/project/ccencrypt/"><img src="https://img.shields.io/pypi/v/ccencrypt?color=6366f1&label=pypi" alt="PyPI"></a>
</p>

| Processor | Function | Type | Returns |
|---|---|---|---|
| Adyen | `ccadyen` | Encrypt | dict of 4 encrypted fields |
| CyberSource Flex | `cccybersource` / `cccybersource_token` | Encrypt / Tokenise | JWE / transient token |
| eWay | `cceway` / `cceway_card` | Encrypt | `eCrypted:...` strings |
| Stripe | `ccstripe` | Tokenise | `pm_...` payment method id |
| Braintree | `ccbraintree` | Tokenise | `tokencc_...` nonce |
| Shopify | `ccshopify` | Tokenise | card session id |
| PayDock | `ccpaydock` | Tokenise | one-time card token |

## Install

```bash
pip install ccencrypt
```

## Card details

Every function cleans the card details before using them, so any of these work:

| Field | Accepted |
|---|---|
| card | `"4242424242424242"`, `"4242 4242 4242 4242"`, `"4242-4242-4242-4242"` |
| month | `1`, `"1"`, `"01"` |
| year | `29`, `"29"`, `2029`, `"2029"` |

Month and year are always separate arguments. If you have `"01/29"`, split it first:

```python
month, year = "01/29".split("/")
```

## Proxies

You can pass a proxy for the process. Some processors like paydock will ratelimit so its important to use proxies:

```python
token = ccencrypt.ccpaydock(public_key, card, month, year, cvv, name, proxy="http://user:pass@host:port")
```

## Errors

Tokenise functions raise `RuntimeError` with the status code and response body when the processor rejects the request.

---

## Encryption

### Adyen

`encrypt_key` is the site's Adyen public key (`10001|A532...`).

```python
import ccencrypt

result = ccencrypt.ccadyen(
    encrypt_key="10001|A532...",
    card="4242424242424242",
    month="12",
    year="2029",
    cvc="123",
    client_key="live_...",
    domain="https://example.com",
)

result["encryptedCardNumber"]
result["encryptedExpiryMonth"]
result["encryptedExpiryYear"]
result["encryptedSecurityCode"]
```

`client_key` and `domain` are optional, but pass the site's own values when you have them.

`version` defaults to `"4.5.0"` (Secured Fields). For sites on legacy encryption (`adyenjs_0_1_XX$...`), pass `"0_1_18"`, `"0_1_22"`, `"0_1_23"`, `"0_1_24"` or `"0_1_25"`. Legacy versions ignore `client_key` and `domain`.

```python
result = ccencrypt.ccadyen(encrypt_key, card, month, year, cvc, version="0_1_25")
```

To encrypt a custom legacy payload such as `holderName`:

```python
from ccencrypt.adyen import parse_public_key

blob = ccencrypt.cse_encrypt(
    {"holderName": "John Smith", "generationtime": "2029-01-01T00:00:00.000Z"},
    parse_public_key("10001|A532..."),
    version="0_1_25",
)
```

### CyberSource Flex

`context` is the capture context JWT from the site's CyberSource init endpoint.

Encrypt and exchange for a transient token in one call:

```python
token = ccencrypt.cccybersource_token(
    card="4242424242424242",
    month="12",
    year="2029",
    cvv="123",
    context=context,
    origin="https://www.example.com",
    user_agent="Mozilla/5.0 ...",
)
```

For Microform sites, pass `microform=True` instead of `origin`.

To encrypt only, use `cccybersource` with the same card arguments and `context`. It returns a JWE that you POST yourself to `https://flex.cybersource.com/flex/v2/tokens` as `application/jwt`.

### eWay

`encrypt_key` is the `data-eway-encrypt-key` value from the site's payment form.

```python
fields = ccencrypt.cceway_card(encrypt_key, card="4242424242424242", cvv="123")

fields["EWAY_CARDNUMBER"]
fields["EWAY_CARDCVN"]
```

To encrypt a single value, use `ccencrypt.cceway(encrypt_key, value)`.

---

## Tokenisation

### Stripe

`key` is the site's publishable key (`pk_live_...`), sent as `key=` in the site's requests to `api.stripe.com`.

```python
pm = ccencrypt.ccstripe(
    key="pk_live_...",
    card="4242424242424242",
    month="12",
    year="2029",
    cvc="123",
    name="John Smith",
)
```

If the site's requests also send `_stripe_account=acct_...`, pass it as `account`.

### Braintree

`client_token` is the base64 client token the site hands to Braintree. A raw `authorizationFingerprint` also works.

```python
nonce = ccencrypt.ccbraintree(
    client_token="eyJ2ZXJzaW9uIjoy...",
    card="4242424242424242",
    month="12",
    year="2029",
    cvv="123",
    name="John Smith",
)
```

### Shopify

`domain` is the store's domain, without `https://` or `www.`.

```python
session_id = ccencrypt.ccshopify(
    domain="example.com.au",
    card="4242424242424242",
    month="12",
    year="2029",
    cvv="123",
    name="John Smith",
)
```

The returned id goes into the checkout's payment as the card `sessionId`.

### PayDock

`public_key` is the site's PayDock public key, sent as `x-user-public-key` in the site's requests to `api.paydock.com`.

```python
token = ccencrypt.ccpaydock(
    public_key="5b12b8af...",
    card="4242424242424242",
    month="12",
    year="2029",
    cvv="123",
    name="John Smith",
)
```

If the site's token request includes a `gateway_id`, pass it as `gateway_id`.
