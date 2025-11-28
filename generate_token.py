#!/usr/bin/env python3
"""Generate a JWT token for testing"""
import jwt
from datetime import datetime, timedelta

# From your .env file
SECRET_KEY = "agape-v3-super-secret-key-min-32-characters-for-jwt-production-2025"
ALGORITHM = "HS256"

# User ID 43 (from your previous token)
user_id = 43

# Create token that expires in 7 days
# NOTE: 'sub' must be a STRING (the app's create_token_pair uses str(user_id))
payload = {
    "sub": str(user_id),  # Convert to string!
    "exp": datetime.utcnow() + timedelta(days=7),
    "type": "access"
}

token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
print(f"Token válido por 7 días:")
print(token)
