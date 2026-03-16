from slowapi import Limiter
from slowapi.util import get_remote_address

# Key function: rate-limit buckets are scoped per client IP address
limiter = Limiter(key_func=get_remote_address)
