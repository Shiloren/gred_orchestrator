from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from ..config import TOKENS
from ..security.auth import SESSION_COOKIE_NAME, _resolve_role, session_store

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    token: str


class LoginResponse(BaseModel):
    role: str
    message: str


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, response: Response, request: Request):
    """Validate a token and set a session cookie. The token is never stored in the browser."""
    token = body.token.strip()
    if not token or len(token) < 16 or token not in TOKENS:
        from ..security.auth import _report_auth_failure
        if token:
            _report_auth_failure(request, token)
        raise HTTPException(status_code=401, detail="Invalid token")

    role = _resolve_role(token)
    cookie_value = session_store.create(role)

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=cookie_value,
        httponly=True,
        samesite="lax",
        secure=False,  # Set True when using HTTPS in production
        max_age=86400,
        path="/",
    )
    return LoginResponse(role=role, message="Authenticated")


@router.post("/logout")
async def logout(request: Request, response: Response):
    """Revoke the session and clear the cookie."""
    cookie_value = request.cookies.get(SESSION_COOKIE_NAME)
    if cookie_value:
        session_store.revoke(cookie_value)
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return {"message": "Logged out"}


@router.get("/check")
async def check_session(request: Request):
    """Check if the current session cookie is valid. No auth required."""
    cookie_value = request.cookies.get(SESSION_COOKIE_NAME)
    if not cookie_value:
        return {"authenticated": False}
    session = session_store.validate(cookie_value)
    if not session:
        return {"authenticated": False}
    return {"authenticated": True, "role": session.role}
