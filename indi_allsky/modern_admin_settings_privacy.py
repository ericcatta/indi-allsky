"""Build a read-only configuration projection without exposing credentials."""
import json

SECRET_TOKENS = ('PASSWORD', 'TOKEN', 'SECRET', 'PRIVATE_KEY', 'APIKEY',
                 'API_KEY', 'ACCESS_KEY', 'APPLICATIONKEY', 'APPLICATION_KEY',
                 'WEBHOOK', 'PSK', 'AUTHORIZATION', 'COOKIE', 'CREDENTIAL')
MASKED = '[redacted]'


def redact_settings(value):
    """Copy nested settings; never alter the configuration used for persistence.

    JSON-encoded profile/driver blocks are inspected too. Boolean switches such
    as ENCRYPT_PASSWORDS remain ordinary settings, not credential values.
    """
    if isinstance(value, dict):
        return {
            key: (MASKED if any(token in str(key).upper() for token in SECRET_TOKENS)
                  and item not in (None, '') and not isinstance(item, bool)
                  else redact_settings(item))
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return type(value)(redact_settings(item) for item in value)
    if isinstance(value, str) and value.lstrip().startswith(('{', '[')):
        try:
            decoded = json.loads(value)
        except ValueError:
            return value
        redacted = redact_settings(decoded)
        return value if redacted == decoded else json.dumps(redacted)
    return value
