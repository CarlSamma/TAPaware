"""OAuth helpers for Twitter/X token refresh and persistence.

Provides a shared refresh routine for OAuth2 PKCE refresh_token flows
and persists updated tokens into the project's `.env` using `save_env_vars`.
"""
from __future__ import annotations

from typing import Optional

import base64
import httpx

from tap.config import Settings, save_env_vars
from tap.logger import get_logger

log = get_logger("oauth")


def _update_settings_tokens(settings: Settings, access_token: str, refresh_token: Optional[str]) -> None:
    """Synchronize in-memory settings with refreshed OAuth2 token values."""
    settings.twitter_oauth2_access_token = access_token
    if refresh_token:
        settings.twitter_oauth2_refresh_token = refresh_token


async def refresh_oauth2_token(settings: Settings) -> Optional[str]:
    """Attempt to refresh OAuth2 user access token using refresh_token.

    Tries PKCE/public client first (client_id in body) then confidential
    client with Basic auth if `client_secret` is present.

    Persists any new refresh token / access token into the `.env`.

    Returns the new access token string, or None if refresh failed.
    """
    refresh_token = settings.twitter_oauth2_refresh_token
    client_id = settings.twitter_oauth2_client_id
    client_secret = settings.twitter_oauth2_client_secret

    if not refresh_token or not client_id:
        log.warning(
            "oauth_refresh_missing_credentials",
            has_refresh=bool(refresh_token),
            has_client_id=bool(client_id),
        )
        return None

    token_url = "https://api.x.com/2/oauth2/token"

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30)) as client:
            # Strategy 1: PKCE / public client
            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
            }
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            resp = await client.post(token_url, headers=headers, data=data)

            if resp.status_code == 200:
                j = resp.json()
                access = j.get("access_token")
                new_refresh = j.get("refresh_token")
                if access:
                    _update_settings_tokens(settings, access, new_refresh)
                    updates = {"TWITTER_OAUTH2_ACCESS_TOKEN": access}
                    if new_refresh:
                        updates["TWITTER_OAUTH2_REFRESH_TOKEN"] = new_refresh
                    save_env_vars(updates)
                    log.info("oauth_refreshed_pkce")
                    return access

            body_text = resp.text[:300]
            log.info("oauth_pkce_refresh_failed", status=resp.status_code, body=body_text)
            try:
                error_body = resp.json()
                if error_body.get("error") or error_body.get("error_description"):
                    log.warning(
                        "oauth_pkce_refresh_error_details",
                        error=error_body.get("error"),
                        error_description=error_body.get("error_description"),
                    )
            except ValueError:
                pass

            # Strategy 2: Confidential client (Basic auth)
            if client_secret:
                creds = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
                headers2 = {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": f"Basic {creds}",
                }
                resp2 = await client.post(
                    token_url,
                    headers=headers2,
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                    },
                )
                if resp2.status_code == 200:
                    j2 = resp2.json()
                    access2 = j2.get("access_token")
                    new_refresh2 = j2.get("refresh_token")
                    if access2:
                        _update_settings_tokens(settings, access2, new_refresh2)
                        updates = {"TWITTER_OAUTH2_ACCESS_TOKEN": access2}
                        if new_refresh2:
                            updates["TWITTER_OAUTH2_REFRESH_TOKEN"] = new_refresh2
                        save_env_vars(updates)
                        log.info("oauth_refreshed_basic_auth")
                        return access2

                body_text2 = resp2.text[:300]
                log.warning(
                    "oauth_basic_auth_refresh_failed",
                    status=resp2.status_code,
                    body=body_text2,
                )
                try:
                    error_body2 = resp2.json()
                    if error_body2.get("error") or error_body2.get("error_description"):
                        log.warning(
                            "oauth_basic_auth_refresh_error_details",
                            error=error_body2.get("error"),
                            error_description=error_body2.get("error_description"),
                        )
                except ValueError:
                    pass
    except Exception as e:
        log.warning("oauth_refresh_exception", error=str(e))

    log.warning("oauth_refresh_all_failed", hint="Refresh token may be expired")
    return None
