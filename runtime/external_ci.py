from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import jwt


class ExternalCIError(RuntimeError):
    pass


def _trim_description(text: str, limit: int = 140) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _parse_repo_from_origin_url(url: str) -> str | None:
    patterns = [
        r"^https://github\.com/([^/]+/[^/.]+?)(?:\.git)?/?$",
        r"^git@github\.com:([^/]+/[^/.]+?)(?:\.git)?$",
    ]
    for pattern in patterns:
        match = re.match(pattern, url.strip())
        if match:
            return match.group(1)
    return None


def _run_git(args: list[str], cwd: Path) -> str:
    completed = subprocess.run(
        args,
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _resolve_repo(explicit_repo: str | None, workspace: Path) -> str:
    if explicit_repo:
        return explicit_repo
    if repo := get_env("GITHUB_REPOSITORY", required=False):
        return repo
    origin = _run_git(["git", "config", "--get", "remote.origin.url"], workspace)
    repo = _parse_repo_from_origin_url(origin)
    if repo:
        return repo
    raise ExternalCIError(
        "Could not resolve repository slug. Pass --repo owner/name or set GITHUB_REPOSITORY."
    )


def _resolve_sha(explicit_sha: str | None, workspace: Path) -> str:
    if explicit_sha:
        return explicit_sha
    if sha := get_env("GITHUB_SHA", required=False):
        return sha
    return _run_git(["git", "rev-parse", "HEAD"], workspace)


def _github_api_request(
    method: str,
    url: str,
    token: str,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    request = Request(url, data=data, method=method)
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    if data is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urlopen(request, timeout=30) as response:
            payload = response.read()
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ExternalCIError(
            f"GitHub API request failed ({method} {url}): HTTP {exc.code} {detail}"
        ) from exc
    if not payload:
        return {}
    return json.loads(payload.decode("utf-8"))


def _load_private_key() -> str:
    inline_key = get_env("GITHUB_APP_PRIVATE_KEY", required=False)
    if inline_key:
        return inline_key.replace("\\n", "\n")
    key_path = get_env("GITHUB_APP_PRIVATE_KEY_PATH", required=False)
    if key_path:
        return Path(key_path).read_text(encoding="utf-8")
    raise ExternalCIError(
        "Missing GitHub App private key. Set GITHUB_APP_PRIVATE_KEY or GITHUB_APP_PRIVATE_KEY_PATH."
    )


def _build_app_jwt(app_id: str, private_key_pem: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "iat": int((now - timedelta(seconds=60)).timestamp()),
        "exp": int((now + timedelta(minutes=9)).timestamp()),
        "iss": app_id,
    }
    encoded = jwt.encode(payload, private_key_pem, algorithm="RS256")
    if isinstance(encoded, bytes):
        return encoded.decode("utf-8")
    return encoded


def _resolve_installation_id(api_url: str, app_jwt: str, repo_slug: str) -> int:
    env_installation_id = get_env("GITHUB_APP_INSTALLATION_ID", required=False)
    if env_installation_id:
        return int(env_installation_id)
    installation = _github_api_request(
        "GET",
        f"{api_url}/repos/{repo_slug}/installation",
        app_jwt,
    )
    installation_id = installation.get("id")
    if not installation_id:
        raise ExternalCIError(
            "Could not resolve GitHub App installation id for repository."
        )
    return int(installation_id)


def _get_github_token(api_url: str, repo_slug: str) -> tuple[str, str]:
    app_id = get_env("GITHUB_APP_ID", required=False)
    if app_id:
        private_key = _load_private_key()
        app_jwt = _build_app_jwt(app_id, private_key)
        installation_id = _resolve_installation_id(api_url, app_jwt, repo_slug)
        access_token = _github_api_request(
            "POST",
            f"{api_url}/app/installations/{installation_id}/access_tokens",
            app_jwt,
            {},
        ).get("token")
        if not access_token:
            raise ExternalCIError("Failed to mint GitHub App installation token.")
        return access_token, "github_app"
    fallback = get_env("GITHUB_TOKEN", required=False)
    if fallback:
        return fallback, "github_token"
    raise ExternalCIError(
        "No auth available. Set GITHUB_APP_ID (+ key) or GITHUB_TOKEN."
    )


def _publish_status(
    api_url: str,
    repo_slug: str,
    sha: str,
    token: str,
    context: str,
    state: str,
    description: str,
    target_url: str | None = None,
) -> None:
    payload: dict[str, Any] = {
        "state": state,
        "context": context,
        "description": _trim_description(description),
    }
    if target_url:
        payload["target_url"] = target_url
    _github_api_request(
        "POST",
        f"{api_url}/repos/{repo_slug}/statuses/{sha}",
        token,
        payload,
    )


def _run_external_command(command: str, workspace: Path) -> int:
    try:
        command_args = shlex.split(command, posix=(os.name != "nt"))
    except ValueError as exc:
        raise ExternalCIError(f"Invalid CI command syntax: {exc}") from exc
    if not command_args:
        raise ExternalCIError("CI command must not be empty.")
    completed = subprocess.run(
        command_args,
        shell=False,
        cwd=str(workspace),
    )
    return int(completed.returncode)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-shell-external-ci",
        description="Run external CI and publish commit status to GitHub.",
    )
    parser.add_argument("--repo", help="GitHub repository slug, for example adaptco/agent-shell")
    parser.add_argument("--sha", help="Commit SHA to update")
    parser.add_argument("--context", default="external-ci", help="Status context name")
    parser.add_argument("--command", default="pytest -q", help="CI command to execute")
    parser.add_argument("--workspace", default=".", help="Workspace root to run the CI command in")
    parser.add_argument("--target-url", default=os.environ.get("EXTERNAL_CI_TARGET_URL"))
    parser.add_argument("--api-url", default=os.environ.get("GITHUB_API_URL", "https://api.github.com"))
    parser.add_argument("--skip-pending", action="store_true", help="Do not publish pending before executing command")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    workspace = Path(args.workspace).resolve()
    repo = _resolve_repo(args.repo, workspace)
    sha = _resolve_sha(args.sha, workspace)
    token, auth_mode = _get_github_token(args.api_url, repo)

    if not args.skip_pending:
        _publish_status(
            args.api_url,
            repo,
            sha,
            token,
            args.context,
            "pending",
            "External CI is running",
            args.target_url,
        )

    started = time.monotonic()
    exit_code = _run_external_command(args.command, workspace)
    elapsed = time.monotonic() - started

    if exit_code == 0:
        state = "success"
        description = f"External CI passed in {elapsed:.1f}s ({auth_mode})"
    else:
        state = "failure"
        description = f"External CI failed in {elapsed:.1f}s ({auth_mode})"

    _publish_status(
        args.api_url,
        repo,
        sha,
        token,
        args.context,
        state,
        description,
        args.target_url,
    )
    return exit_code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ExternalCIError as exc:
        print(f"[external-ci] {exc}", file=sys.stderr)
        sys.exit(2)
