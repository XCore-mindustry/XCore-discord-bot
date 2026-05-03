from __future__ import annotations

from typing import Any

LEGACY_HEARTBEAT_ALIASES: dict[str, str] = {
    "server_name": "serverName",
    "discord_channel_id": "discordChannelId",
    "max_players": "maxPlayers",
    "player_count": "players",
}


def normalize_server_heartbeat_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Translate legacy snake_case heartbeat fields to canonical keys.

    Returns a new dict with only canonical keys (legacy keys are stripped).
    """
    normalized: dict[str, Any] = {}
    for k, v in payload.items():
        if k in LEGACY_HEARTBEAT_ALIASES:
            canonical = LEGACY_HEARTBEAT_ALIASES[k]
            normalized.setdefault(canonical, v)
        else:
            normalized[k] = v
    return normalized


def normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return normalize_server_heartbeat_payload(payload)


__all__ = [
    "LEGACY_HEARTBEAT_ALIASES",
    "normalize_payload",
    "normalize_server_heartbeat_payload",
]
