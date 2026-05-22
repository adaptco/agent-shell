from __future__ import annotations
from runtime.utils import get_env
from dataclasses import dataclass
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient


@dataclass
class OperatorIdentity:
    subject: str
    email: str | None
    groups: list[str]
    scopes: list[str]
    auth_mode: str


class ServiceBoundaryAuth:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.service_cfg = cfg.get("auth", {}).get("service_boundary", {})
        self.bearer = HTTPBearer(auto_error=False)

    def _disabled_identity(self) -> OperatorIdentity:
        return OperatorIdentity(subject="anonymous", email=None, groups=[], scopes=[], auth_mode="disabled")

    def _from_proxy_headers(self, request: Request) -> OperatorIdentity:
        hdrs = {k.lower(): v for k, v in request.headers.items()}
        user = hdrs.get("x-auth-request-user")
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing trusted proxy identity")
        email = hdrs.get("x-auth-request-email")
        groups = [g.strip() for g in (hdrs.get("x-auth-request-groups") or "").split(",") if g.strip()]
        return OperatorIdentity(subject=user, email=email, groups=groups, scopes=[], auth_mode="trusted_proxy_oidc")

    def _from_static_bearer(self, credentials: HTTPAuthorizationCredentials | None) -> OperatorIdentity:
        token = get_env(self.service_cfg.get("static_bearer_env_var", "AGENT_SERVICE_BEARER_TOKEN"), required=False)
        if not token:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Static bearer token is not configured")
        if credentials is None or credentials.credentials != token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid operator token")
        return OperatorIdentity(subject="operator", email=None, groups=["operators"], scopes=["agent:operate"], auth_mode="static_bearer")

    @lru_cache(maxsize=2)
    def _jwks_client(self, jwks_url: str) -> PyJWKClient:
        return PyJWKClient(jwks_url)

    def _from_oidc_jwt(self, credentials: HTTPAuthorizationCredentials | None) -> OperatorIdentity:
        if credentials is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
        oidc_cfg = self.service_cfg.get("oidc", {})
        issuer = oidc_cfg.get("issuer")
        audience = oidc_cfg.get("audience")
        jwks_url = oidc_cfg.get("jwks_url")
        if not issuer or not audience or not jwks_url:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="OIDC service boundary is not configured")
        signing_key = self._jwks_client(jwks_url).get_signing_key_from_jwt(credentials.credentials).key
        payload = jwt.decode(
            credentials.credentials,
            signing_key,
            algorithms=["RS256", "ES256"],
            audience=audience,
            issuer=issuer,
        )
        token_scopes = payload.get("scope", "")
        if isinstance(token_scopes, str):
            token_scopes = [s for s in token_scopes.split(" ") if s]
        required = oidc_cfg.get("required_scopes", [])
        missing = [scope for scope in required if scope not in token_scopes]
        if missing:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Missing scopes: {', '.join(missing)}")
        groups = payload.get("groups") or payload.get("roles") or []
        if isinstance(groups, str):
            groups = [groups]
        return OperatorIdentity(
            subject=payload.get("sub", "unknown"),
            email=payload.get("email"),
            groups=list(groups),
            scopes=list(token_scopes),
            auth_mode="oidc_jwt",
        )

    async def authenticate(self, request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False))) -> OperatorIdentity:
        if not self.service_cfg.get("enabled", False):
            return self._disabled_identity()
        mode = self.service_cfg.get("mode", "disabled")
        if mode == "disabled":
            return self._disabled_identity()
        if mode == "trusted_proxy_oidc":
            return self._from_proxy_headers(request)
        if mode == "static_bearer":
            return self._from_static_bearer(credentials)
        if mode == "oidc_jwt":
            return self._from_oidc_jwt(credentials)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unsupported auth mode: {mode}")


def get_auth_dependency(cfg: dict):
    boundary = ServiceBoundaryAuth(cfg)

    async def _dependency(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(boundary.bearer)) -> OperatorIdentity:
        return await boundary.authenticate(request, credentials)

    return _dependency
