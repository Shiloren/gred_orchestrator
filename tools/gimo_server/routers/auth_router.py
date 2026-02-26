import logging

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from ..config import GIMO_INTERNAL_KEY, GIMO_WEB_URL, TOKENS
from ..security.auth import (
    FIREBASE_SESSION_TTL,
    SESSION_COOKIE_NAME,
    _resolve_role,
    session_store,
)

logger = logging.getLogger("orchestrator.auth_router")

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    token: str


class LoginResponse(BaseModel):
    role: str
    message: str


class FirebaseLoginRequest(BaseModel):
    idToken: str


def _is_secure_request(request: Request) -> bool:
    forwarded_proto = request.headers.get("x-forwarded-proto", "").lower()
    if forwarded_proto == "https":
        return True
    return request.url.scheme == "https"


def _map_firebase_role_to_session_role(firebase_role: str) -> str:
    """
    Maps GIMO WEB role model (user/admin) to orchestrator RBAC role model
    (actions/operator/admin).
    """
    if firebase_role == "admin":
        return "admin"
    return "operator"


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
        secure=_is_secure_request(request),
        max_age=86400,
        path="/",
    )
    return LoginResponse(role=role, message="Authenticated")


@router.post("/firebase-login")
async def firebase_login(body: FirebaseLoginRequest, response: Response, request: Request):
    """Authenticate using Firebase ID token via GIMO WEB verify endpoint."""
    id_token = body.idToken.strip()
    if not id_token:
        raise HTTPException(status_code=400, detail="idToken required")

    if not GIMO_INTERNAL_KEY:
        raise HTTPException(status_code=500, detail="GIMO_INTERNAL_KEY is not configured")

    verify_url = f"{GIMO_WEB_URL.rstrip('/')}/api/orchestrator/verify"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            verify_response = await client.post(
                verify_url,
                json={"idToken": id_token},
                headers={"X-Internal-Key": GIMO_INTERNAL_KEY},
            )
    except httpx.HTTPError as exc:
        logger.warning("Firebase verify request failed: %s", exc)
        raise HTTPException(status_code=502, detail="Unable to reach auth upstream") from exc

    if verify_response.status_code in (401, 403):
        raise HTTPException(status_code=401, detail="Invalid Firebase token")
    if verify_response.status_code >= 400:
        raise HTTPException(status_code=502, detail="Auth upstream rejected request")

    payload = verify_response.json()
    firebase_role = payload.get("role") if payload.get("role") in ("admin", "user") else "user"
    role = _map_firebase_role_to_session_role(firebase_role)
    email = str(payload.get("email") or "")
    display_name = str(payload.get("displayName") or "")

    license_data = payload.get("license") or {}
    plan = str(license_data.get("plan") or "none")

    cookie_value = session_store.create(
        role=role,
        uid=str(payload.get("uid") or ""),
        email=email,
        display_name=display_name,
        plan=plan,
        firebase_user=True,
        profile_cache={
            "license": license_data,
            "subscription": payload.get("subscription") or {},
        },
    )

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=cookie_value,
        httponly=True,
        samesite="lax",
        secure=_is_secure_request(request),
        max_age=FIREBASE_SESSION_TTL,
        path="/",
    )

    return {
        "role": role,
        "firebaseRole": firebase_role,
        "email": email,
        "displayName": display_name,
        "plan": plan,
    }


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

    data = {
        "authenticated": True,
        "role": session.role,
    }

    if session.firebase_user:
        data.update(
            {
                "email": session.email,
                "displayName": session.display_name,
                "plan": session.plan,
                "firebaseUser": True,
                "sessionRole": session.role,
            }
        )

    return data


@router.get("/profile")
async def profile(request: Request):
    """Return full profile for authenticated session, refreshing from GIMO WEB for Firebase users."""
    cookie_value = request.cookies.get(SESSION_COOKIE_NAME)
    if not cookie_value:
        raise HTTPException(status_code=401, detail="Session missing")

    session = session_store.validate(cookie_value)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired")

    if not session.firebase_user:
        session_info = session_store.get_session_info(cookie_value)
        if not session_info:
            raise HTTPException(status_code=401, detail="Session expired")
        return {
            "user": {
                "role": session.role,
                "email": session.email,
                "displayName": session.display_name,
            },
            "license": {
                "plan": session.plan or "none",
                "status": "none",
                "isLifetime": False,
                "keyPreview": "",
                "installationsUsed": 0,
                "installationsMax": 0,
                "expiresAt": None,
            },
            "subscription": {
                "status": "none",
                "currentPeriodEnd": None,
                "cancelAtPeriodEnd": False,
            },
            "session": session_info,
        }

    upstream_payload = None
    if GIMO_INTERNAL_KEY and GIMO_WEB_URL:
        verify_url = f"{GIMO_WEB_URL.rstrip('/')}/api/orchestrator/verify"
        try:
            auth_header = request.headers.get("Authorization", "")
            id_token = ""
            if auth_header.lower().startswith("bearer "):
                id_token = auth_header[7:].strip()

            if id_token:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    upstream = await client.post(
                        verify_url,
                        json={"idToken": id_token},
                        headers={"X-Internal-Key": GIMO_INTERNAL_KEY},
                    )
                if upstream.status_code < 400:
                    upstream_payload = upstream.json()
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning("Profile refresh from upstream failed, using cache: %s", exc)

    if upstream_payload:
        session.email = str(upstream_payload.get("email") or session.email)
        session.display_name = str(upstream_payload.get("displayName") or session.display_name)
        session.plan = str((upstream_payload.get("license") or {}).get("plan") or session.plan)
        session.profile_cache = {
            "license": upstream_payload.get("license") or {},
            "subscription": upstream_payload.get("subscription") or {},
        }

    license_data = session.profile_cache.get("license") or {
        "plan": session.plan or "none",
        "status": "none",
        "isLifetime": False,
        "keyPreview": "",
        "installationsUsed": 0,
        "installationsMax": 0,
        "expiresAt": None,
    }
    subscription_data = session.profile_cache.get("subscription") or {
        "status": "none",
        "currentPeriodEnd": None,
        "cancelAtPeriodEnd": False,
    }

    session_info = session_store.get_session_info(cookie_value)
    if not session_info:
        raise HTTPException(status_code=401, detail="Session expired")

    return {
        "user": {
            "uid": session.uid,
            "role": session.role,
            "email": session.email,
            "displayName": session.display_name,
        },
        "license": license_data,
        "subscription": subscription_data,
        "profileSource": "upstream" if upstream_payload else "session_cache",
        "session": session_info,
    }
