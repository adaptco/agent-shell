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

## FastAPI note

FastAPI can declare OpenID Connect in OpenAPI docs, but its `OpenIdConnect` helper is only a stub and does not implement full verification by itself. That is why this build implements service-boundary verification in `runtime/api_auth.py` instead of pretending the framework does it for you.

## External CI status publisher authentication

Branch protection can require the `external-ci` status context without using GitHub Actions minutes.
The external publisher (`agent-shell-external-ci`) supports:

1. **GitHub App installation token (recommended)**
   - `GITHUB_APP_ID`
   - `GITHUB_APP_PRIVATE_KEY_PATH` or `GITHUB_APP_PRIVATE_KEY`
   - Optional `GITHUB_APP_INSTALLATION_ID`
2. **Fallback token**
   - `GITHUB_TOKEN`

For GitHub App mode, the app should have commit status write permission and be installed on this repository.
