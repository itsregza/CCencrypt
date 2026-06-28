# dynamiteencrypt

Python card encryption for **Adyen**, **CyberSource Flex**, and **eWay**.

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
    encrypt_key="10001|A53214687356F8E86F1D6057C95EFAFB913DC2E7E7997E3927A87C42CBCAD46E425A8069EA11EBC44B052CF78D8D3022214FFC7453DD4151BE17E6232C4ECB77E0B6F5BE4DD6E6D28C0E5AE8C287528A8474E1E327AAE6BBE32E84538D3B28DAB0338C260BF4A008974F45CEF86B1D5634FAD85FAFAC17019082DD1AB3A78A9116334620A82EB2C986D65422ED20DB16094D5A7CBFC0FA936D0444B189719BE71A13AA8734E38CF37D94F35A2C0B519F5BDDA750CB6A8EE90F904A94D4BD653C0179D9BF93D9D160D26327BA76369221DA2F0AC0260580643E09479300E46F38ADD155F89D245E4260CAEDB72A144CB364AC9B97ADE35E27B46A7C887CBEEFD3",
    card="4242424242424242",
    month="12",
    year="2029",
    cvc="123",
    client_key="live_SQV7J3WVMNFK3HU33BTUNF5AH4E2L2ZN",   # optional
    domain="https://minisoshop.co.uk",  # optional
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

### eWay

Use the `data-eway-encrypt-key` value from the merchant form (base64 modulus blob).

```python
import dynamiteencrypt

encrypted_pan = dynamiteencrypt.dynamiteeway(encrypt_key, "4242424242424242")
encrypted_cvv = dynamiteencrypt.dynamiteeway(encrypt_key, "123")

# or both at once for EWAY form fields
fields = dynamiteencrypt.dynamiteeway_card(
    encrypt_key,
    card="4242424242424242",
    cvv="123",
)
# fields["EWAY_CARDNUMBER"], fields["EWAY_CARDCVN"]
```

Returns strings prefixed with `eCrypted:` as eWay expects.

## Requirements

- Python 3.9+
- cryptography
