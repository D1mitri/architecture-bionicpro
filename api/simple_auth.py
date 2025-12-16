from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import hashlib
import uuid
import base64
import json
import logging

logger = logging.getLogger(__name__)
security = HTTPBearer()

def generate_user_guid(username: str, email: str) -> str:
    unique_string = f"{username}:{email}"

    hash_md5 = hashlib.md5(unique_string.encode('utf-8')).hexdigest()

    return str(uuid.UUID(hash_md5))

def generate_user_id_from_guid(guid: str) -> int:

    hex_part = guid.replace('-', '')[:8]
    user_id = int(hex_part, 16) % 1000 + 1

    return user_id

async def get_current_user_simple(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials

    try:
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid JWT format")

        payload_b64 = parts[1]

        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += '=' * padding

        payload_bytes = base64.b64decode(payload_b64)
        payload = json.loads(payload_bytes)

        username = payload.get('preferred_username', 'unknown')
        email = payload.get('email', 'unknown@example.com')

        user_guid = generate_user_guid(username, email)

        user_id = generate_user_id_from_guid(user_guid)

        logger.info(f"User auth: username={username}, email={email}, guid={user_guid}, user_id={user_id}")

        return {
            "sub": payload.get('sub', ''),
            "preferred_username": username,
            "email": email,
            "user_guid": user_guid,
            "user_id": user_id,
            "token_info": {
                "iss": payload.get('iss', ''),
                "roles": payload.get('realm_access', {}).get('roles', [])
            }
        }

    except Exception as e:
        logger.error(f"Authentication error: {e}")

        fallback_guid = str(uuid.uuid4())
        fallback_user_id = generate_user_id_from_guid(fallback_guid)

        return {
            "sub": "fallback-user",
            "preferred_username": "fallback",
            "email": "fallback@example.com",
            "user_guid": fallback_guid,
            "user_id": fallback_user_id,
            "token_info": {}
        }