# dynamiteencrypt

Python card encryption for **Adyen 4.5.0** and **CyberSource Flex**.

No Node.js required.

## Install

From GitHub:

```bash
pip install git+https://github.com/itsregza/dynamiteencrypt.git
```

Local dev:

```bash
pip install -e ./dynamiteencrypt
```

## Usage

### Adyen

```python
import dynamiteencrypt

result = dynamiteencrypt.dynamiteadyen(
    adyen_key="10001|...",
    card="4242424242424242",
    month="12",
    year="2029",
    cvc="123",
    stripe_key="live_...",   # optional
    domain="https://example.com",  # optional
)

print(result["encryptedCardNumber"])
print(result["encryptedExpiryMonth"])
print(result["encryptedExpiryYear"])
print(result["encryptedSecurityCode"])
```

### CyberSource

You need a `context` JWT from the merchant init endpoint first (e.g. `/cybersource/init`).

```python
import dynamiteencrypt

token = dynamiteencrypt.dynamitecybersource(
    card="4242424242424242",
    month="12",
    year="2029",
    cvv="123",
    context=context_jwt_from_init,
)
```

Post `token` to `https://flex.cybersource.com/flex/v2/tokens` as `application/jwt`.

## Requirements

- Python 3.9+
- cryptography
