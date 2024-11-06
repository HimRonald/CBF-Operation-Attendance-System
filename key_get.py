import os
import secrets

# Generate a secure random key
secret_key = secrets.token_hex(24)
print(secret_key)
