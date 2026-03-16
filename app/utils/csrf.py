import secrets


def generate_csrf_token(nbytes: int = 32) -> str:
    """Return a cryptographically secure random CSRF token (hex string)."""
    return secrets.token_hex(nbytes)


def validate_csrf_token(provided: str, expected: str) -> bool:
    """Constant-time comparison to prevent timing attacks."""
    return secrets.compare_digest(provided, expected)
