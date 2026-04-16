# Authentication Model

## Provider authentication

Provider authentication stays server-side.
Clients never send OpenAI or Mistral API keys to the inbound FastAPI service.

Environment variables used by the runtime:

- `OPENAI_API_KEY`
- `MISTRAL_API_KEY`

Those are consumed only by `runtime/llm.py`.

## Service-boundary authentication

This build adds a separate auth boundary for operators/users calling the inbound API.
Configured in `infra/runtime.json`:

- `disabled`
- `static_bearer`
- `trusted_proxy_oidc`
- `oidc_jwt`

Mode behavior is fail-closed:

- unknown mode -> HTTP 500 (misconfiguration)
- missing static bearer token -> HTTP 500 (server misconfigured)
- missing/invalid caller credentials -> HTTP 401
- missing required OIDC scopes -> HTTP 403

### Why split auth this way

The runtime has two different trust problems:

1. **Who is allowed to call the service?**
   - solved at the app/service boundary with bearer tokens or OIDC.
2. **How does the runtime call providers?**
   - solved with server-side API keys.

Those are not the same thing and should not share the same credential.

## OIDC guidance

For production, prefer one of these:

### `trusted_proxy_oidc`
Put the FastAPI service behind a gateway or reverse proxy that already performs OIDC login.
The proxy forwards trusted identity headers to the service.
This is the cleanest cut when you already have a platform gateway.

### `oidc_jwt`
Use direct bearer tokens from an OIDC provider.
The service verifies issuer, audience, and JWKS signatures before allowing access.

This mode is intended when no trusted identity proxy sits in front of the service.
It keeps verification in-process and emits operator context only after signature and scope checks pass.

## FastAPI note

FastAPI can declare OpenID Connect in OpenAPI docs, but its `OpenIdConnect` helper is only a stub and does not implement full verification by itself. That is why this build implements service-boundary verification in `runtime/api_auth.py` instead of pretending the framework does it for you.
