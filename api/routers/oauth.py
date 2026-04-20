from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from api.core.database import get_db
from api.core.oauth import verify_google_token, verify_apple_token
from api.services.oauth_service import OAuthService
from api.schemas.auth import TokenResponse

router = APIRouter(prefix="/auth", tags=["OAuth"])


class GoogleSignInRequest(BaseModel):
    id_token: str


class AppleSignInRequest(BaseModel):
    identity_token: str
    full_name: str = ""


@router.post("/google", response_model=TokenResponse)
async def google_signin(body: GoogleSignInRequest, db: Session = Depends(get_db)):
    """
    Accepts the Google ID token from the frontend after the user
    completes Google Sign-In. Works for both sign-in and sign-up —
    a new account is created automatically if the email is not registered.
    """
    provider_data = await verify_google_token(body.id_token)
    return OAuthService(db).authenticate(provider_data)


@router.post("/apple", response_model=TokenResponse)
async def apple_signin(body: AppleSignInRequest, db: Session = Depends(get_db)):
    """
    Accepts the Apple identity token from the frontend after the user
    completes Sign in with Apple. full_name is only sent by Apple on
    the very first sign-in — store it then, it won't come again.
    """
    provider_data = await verify_apple_token(body.identity_token)
    if body.full_name:
        provider_data["full_name"] = body.full_name
    return OAuthService(db).authenticate(provider_data)