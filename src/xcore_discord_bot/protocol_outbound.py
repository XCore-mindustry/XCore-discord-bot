from __future__ import annotations

from datetime import datetime, timezone

from xcore_protocol.generated.discord import (
    DiscordAdminAccessChangedCommandV1,
    DiscordLinkConfirmCommandV1,
    DiscordUnlinkCommandV1,
)
from xcore_protocol.generated.moderation import (
    ModerationKickBannedCommandV1,
    ModerationPardonCommandV1,
)
from xcore_protocol.generated.shared import (
    ActorRefV1,
    ActorRefV1ActorType,
    DiscordIdentityRefV1,
    PlayerCommandTargetV1,
    PlayerRefV1,
)


def utc_now_iso8601() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def build_moderation_kick_banned_command(
    uuid_value: str,
    ip: str | None,
    server: str,
) -> ModerationKickBannedCommandV1:
    return ModerationKickBannedCommandV1(
        target=PlayerCommandTargetV1(
            playerUuid=uuid_value or None,
            ip=ip,
        ),
        server=server,
        requestedAt=utc_now_iso8601(),
    )


def build_moderation_pardon_command(
    uuid_value: str,
    server: str,
) -> ModerationPardonCommandV1:
    return ModerationPardonCommandV1(
        target=PlayerCommandTargetV1(
            playerUuid=uuid_value,
        ),
        server=server,
        requestedAt=utc_now_iso8601(),
    )


def build_discord_link_confirm_command(
    code: str,
    player_uuid: str,
    player_pid: int,
    player_name: str,
    discord_id: str,
    discord_username: str,
    server: str,
) -> DiscordLinkConfirmCommandV1:
    return DiscordLinkConfirmCommandV1(
        code=code,
        player=PlayerRefV1(
            playerUuid=player_uuid,
            playerPid=player_pid,
            playerName=player_name,
        ),
        discord=DiscordIdentityRefV1(
            discordId=discord_id,
            discordUsername=discord_username,
        ),
        server=server,
        confirmedAt=utc_now_iso8601(),
    )


def build_discord_unlink_command(
    player_uuid: str,
    player_pid: int,
    player_name: str,
    discord_id: str,
    discord_username: str,
    actor_name: str,
    actor_discord_id: str,
    server: str,
) -> DiscordUnlinkCommandV1:
    return DiscordUnlinkCommandV1(
        player=PlayerRefV1(
            playerUuid=player_uuid,
            playerPid=player_pid,
            playerName=player_name,
        ),
        discord=DiscordIdentityRefV1(
            discordId=discord_id,
            discordUsername=discord_username,
        ),
        actor=ActorRefV1(
            actorName=actor_name,
            actorDiscordId=actor_discord_id,
            actorType=ActorRefV1ActorType.DISCORD,
        ),
        server=server,
        requestedAt=utc_now_iso8601(),
    )


def build_discord_admin_access_changed_command(
    player_uuid: str,
    player_pid: int,
    player_name: str,
    discord_id: str,
    discord_username: str | None,
    admin: bool,
    source_name: str,
    source_type: ActorRefV1ActorType,
    actor_name: str,
    actor_discord_id: str | None,
    actor_type: ActorRefV1ActorType,
    reason: str,
    server: str,
) -> DiscordAdminAccessChangedCommandV1:
    return DiscordAdminAccessChangedCommandV1(
        player=PlayerRefV1(
            playerUuid=player_uuid,
            playerPid=player_pid,
            playerName=player_name,
        ),
        discord=DiscordIdentityRefV1(
            discordId=discord_id,
            discordUsername=discord_username,
        ),
        admin=admin,
        source=ActorRefV1(
            actorName=source_name,
            actorType=source_type,
        ),
        actor=ActorRefV1(
            actorName=actor_name,
            actorDiscordId=actor_discord_id,
            actorType=actor_type,
        ),
        reason=reason,
        server=server,
        occurredAt=utc_now_iso8601(),
    )
