import httpx
from fastapi import HTTPException
from api.core.config import settings


GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"
APPLE_KEYS_URL = "https://appleid.apple.com/auth/keys"
APPLE_ISSUER = "https://appleid.apple.com"


async def verify_google_token(id_token: str) -> dict:
    """
    Verify a Google ID token returned from the frontend
    after the user completes Google Sign-In.
    Returns the decoded payload with email, name, sub (google user id).
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GOOGLE_TOKEN_INFO_URL,
            params={"id_token": id_token},
        )

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    data = response.json()

    if data.get("aud") != settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=401, detail="Google token audience mismatch")

    if not data.get("email_verified"):
        raise HTTPException(status_code=401, detail="Google email not verified")

    return {
        "provider": "google",
        "provider_id": data["sub"],
        "email": data["email"],
        "full_name": data.get("name", data["email"].split("@")[0]),
        "avatar_url": data.get("picture"),
    }


async def verify_apple_token(identity_token: str) -> dict:
    """
    Verify an Apple identity token returned from the frontend
    after the user completes Sign in with Apple.
    Returns decoded payload with email and sub (apple user id).
    """
    try:
        import jwt as pyjwt
        from jwt.algorithms import RSAAlgorithm
        import json
    except ImportError:
        raise HTTPException(status_code=501, detail="Install PyJWT: pip install PyJWT cryptography")

    async with httpx.AsyncClient() as client:
        keys_response = await client.get(APPLE_KEYS_URL)

    if keys_response.status_code != 200:
        raise HTTPException(status_code=401, detail="Could not fetch Apple public keys")

    apple_keys = keys_response.json().get("keys", [])

    header = pyjwt.get_unverified_header(identity_token)
    kid = header.get("kid")

    matching_key = next((k for k in apple_keys if k["kid"] == kid), None)
    if not matching_key:
        raise HTTPException(status_code=401, detail="Apple signing key not found")

    public_key = RSAAlgorithm.from_jwk(json.dumps(matching_key))

    try:
        payload = pyjwt.decode(
            identity_token,
            public_key,
            algorithms=["RS256"],
            audience=settings.APPLE_CLIENT_ID,
            issuer=APPLE_ISSUER,
        )
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Apple token expired")
    except pyjwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Apple token: {str(e)}")

    return {
        "provider": "apple",
        "provider_id": payload["sub"],
        "email": payload.get("email", ""),
        "full_name": "",
    }