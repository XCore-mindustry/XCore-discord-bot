from __future__ import annotations

from datetime import datetime, timezone
from json import loads
from enum import StrEnum
from typing import Any, ClassVar

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
)
from xcore_protocol.generated import (
    ChatGlobalV1,
    ChatMessageV1,
    DiscordLinkStatusChangedV1,
    ModerationBanCreatedV1,
    ModerationMuteCreatedV1,
    ModerationVoteKickCreatedV1,
    PlayerJoinLeaveV1,
    ServerActionV1,
    ServerHeartbeatV1,
)
from xcore_protocol.generated.discord import DiscordLinkStatusChangedV1Action
from xcore_protocol.generated.shared import (
    ActorRefV1,
    ActorRefV1ActorType,
    DiscordIdentityRefV1,
    ExpirationInfoV1,
    PlayerRefV1,
    VoteKickParticipantV1,
)


class _FrozenModel(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True,
        extra="ignore",
        populate_by_name=True,
    )

    @staticmethod
    def _require_non_empty_text(value: str) -> str:
        if not value:
            raise ValueError("Expected non-empty string")
        return value

    @classmethod
    def _validate_payload(
        cls,
        payload: dict[str, Any],
        *,
        error_message: str,
    ):
        try:
            return cls.model_validate(payload)
        except ValidationError as error:
            raise ValueError(error_message) from error


class EventType(StrEnum):
    HEARTBEAT = "ServerHeartbeatEvent"


LEGACY_HEARTBEAT_EVENT_TYPES = frozenset(
    {
        EventType.HEARTBEAT,
        "org.xcore.plugin.event.SocketEvents$ServerHeartbeatEvent",
        "event.serverheartbeatevent",
    }
)


def _coerce_int(value: Any) -> int:
    if isinstance(value, bool):
        raise ValueError("Expected integer value")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        normalized = value.strip()
        if normalized and normalized.lstrip("-").isdigit():
            return int(normalized)
    raise ValueError("Expected integer value")


def _epoch_millis_to_iso8601(value: int) -> str:
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).isoformat(
        timespec="milliseconds"
    )


class _LegacyGameChatPayload(_FrozenModel):
    author_name: str = Field(validation_alias=AliasChoices("authorName", "author_name"))
    message: str
    server: str

    @field_validator("author_name", "message", "server")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        return cls._require_non_empty_text(value)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "_LegacyGameChatPayload":
        return cls._validate_payload(
            payload,
            error_message="Invalid chat payload: expected authorName, message, server",
        )


def parse_chat_message_payload(payload: dict[str, Any]) -> ChatMessageV1:
    try:
        return ChatMessageV1.from_payload(payload)
    except (TypeError, ValueError):
        legacy = _LegacyGameChatPayload.from_payload(payload)
        return ChatMessageV1(
            authorName=legacy.author_name,
            message=legacy.message,
            server=legacy.server,
        )


class _LegacyPlayerJoinLeavePayload(_FrozenModel):
    player_name: str = Field(validation_alias=AliasChoices("playerName", "player_name"))
    server: str
    joined: bool = Field(validation_alias="join")

    @field_validator("player_name", "server")
    @classmethod
    def _required_text(cls, value: str) -> str:
        return cls._require_non_empty_text(value)

    @field_validator("joined", mode="before")
    @classmethod
    def _parse_joined(cls, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"true", "1", "yes", "on"}
        if isinstance(value, (int, float)):
            return value != 0
        return False

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "_LegacyPlayerJoinLeavePayload":
        return cls._validate_payload(
            payload,
            error_message="Invalid join/leave payload: expected playerName and server",
        )


def parse_player_join_leave_payload(payload: dict[str, Any]) -> PlayerJoinLeaveV1:
    try:
        return PlayerJoinLeaveV1.from_payload(payload)
    except (TypeError, ValueError):
        legacy = _LegacyPlayerJoinLeavePayload.from_payload(payload)
        return PlayerJoinLeaveV1(
            playerName=legacy.player_name,
            server=legacy.server,
            joined=legacy.joined,
        )


class _LegacyServerActionPayload(_FrozenModel):
    message: str
    server: str

    @field_validator("message", "server")
    @classmethod
    def _required_text(cls, value: str) -> str:
        return cls._require_non_empty_text(value)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "_LegacyServerActionPayload":
        return cls._validate_payload(
            payload,
            error_message="Invalid server action payload: expected message and server",
        )


def parse_server_action_payload(payload: dict[str, Any]) -> ServerActionV1:
    try:
        return ServerActionV1.from_payload(payload)
    except (TypeError, ValueError):
        legacy = _LegacyServerActionPayload.from_payload(payload)
        return ServerActionV1(
            message=legacy.message,
            server=legacy.server,
        )


class _LegacyBanPayload(_FrozenModel):
    pid: int | None = Field(
        default=None,
        validation_alias=AliasChoices("pid", "playerPid", "player_pid"),
    )
    uuid: str | None = None
    ip: str | None = None
    name: str
    admin_name: str = Field(validation_alias=AliasChoices("adminName", "admin_name"))
    admin_discord_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("adminDiscordId", "admin_discord_id"),
    )
    reason: str
    expire_date: str | None = Field(
        default=None,
        validation_alias=AliasChoices("expireDate", "expire_date"),
    )

    @field_validator("name", "admin_name", "reason")
    @classmethod
    def _required_text(cls, value: str) -> str:
        return cls._require_non_empty_text(value)

    @field_validator("pid", mode="before")
    @classmethod
    def _optional_int(cls, value: Any) -> int | None:
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        return _coerce_int(value)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "_LegacyBanPayload":
        return cls._validate_payload(
            payload,
            error_message="Invalid ban payload: expected name, adminName/admin_name, reason",
        )


class _LegacyMutePayload(_FrozenModel):
    pid: int | None = Field(
        default=None,
        validation_alias=AliasChoices("pid", "playerPid", "player_pid"),
    )
    uuid: str | None = None
    name: str
    admin_name: str = Field(validation_alias=AliasChoices("adminName", "admin_name"))
    admin_discord_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("adminDiscordId", "admin_discord_id"),
    )
    reason: str
    expire_date: str | None = Field(
        default=None,
        validation_alias=AliasChoices("expireDate", "expire_date"),
    )

    @field_validator("name", "admin_name", "reason")
    @classmethod
    def _required_text(cls, value: str) -> str:
        return cls._require_non_empty_text(value)

    @field_validator("pid", mode="before")
    @classmethod
    def _optional_int(cls, value: Any) -> int | None:
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        return _coerce_int(value)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "_LegacyMutePayload":
        return cls._validate_payload(
            payload,
            error_message="Invalid mute payload: expected name, adminName/admin_name, reason",
        )


class VoteKickParticipant(_FrozenModel):
    name: str = Field(
        validation_alias=AliasChoices("name", "nickname", "playerName", "player_name")
    )
    pid: int | None = Field(
        default=None,
        validation_alias=AliasChoices("pid", "playerPid", "player_pid"),
    )
    discord_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("discordId", "discord_id"),
    )

    @field_validator("name")
    @classmethod
    def _required_text(cls, value: str) -> str:
        return cls._require_non_empty_text(value)

    @field_validator("pid", mode="before")
    @classmethod
    def _optional_int(cls, value: Any) -> int | None:
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        return _coerce_int(value)


def _build_player_ref(
    *,
    uuid: str | None,
    name: str,
    pid: int | None = None,
    ip: str | None = None,
) -> PlayerRefV1:
    normalized_uuid = str(uuid or "").strip()
    if not normalized_uuid:
        normalized_uuid = f"legacy:{str(name).strip() or 'unknown'}"
    return PlayerRefV1(
        playerUuid=normalized_uuid,
        playerName=name,
        playerPid=pid,
        ip=ip,
    )


def _build_actor_ref(*, name: str, discord_id: str | None) -> ActorRefV1:
    normalized_discord_id = str(discord_id or "").strip() or None
    actor_type = (
        ActorRefV1ActorType.DISCORD
        if normalized_discord_id is not None
        else ActorRefV1ActorType.UNKNOWN
    )
    return ActorRefV1(
        actorName=name,
        actorDiscordId=normalized_discord_id,
        actorType=actor_type,
    )


def _build_expiration_info(expire_date: str | None) -> ExpirationInfoV1 | None:
    normalized_expire_date = str(expire_date or "").strip()
    if not normalized_expire_date:
        return None
    return ExpirationInfoV1(expiresAt=normalized_expire_date)


def _normalize_vote_kick_participants(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    raise ValueError("Expected participant list")


def _parse_vote_kick_participants(value: Any) -> tuple[VoteKickParticipantV1, ...]:
    participants = _normalize_vote_kick_participants(value)
    return tuple(
        _to_generated_vote_kick_participant(VoteKickParticipant.model_validate(item))
        for item in participants
    )


def _to_generated_vote_kick_participant(
    participant: VoteKickParticipant,
) -> VoteKickParticipantV1:
    return VoteKickParticipantV1(
        playerName=participant.name,
        playerPid=participant.pid,
        discordId=participant.discord_id,
    )


def _vote_kick_participant_matches_starter(
    participant: VoteKickParticipantV1,
    *,
    starter_name: str,
    starter_pid: int | None,
    starter_discord_id: str | None,
) -> bool:
    normalized_discord_id = str(starter_discord_id or "").strip() or None
    participant_discord_id = str(participant.discordId or "").strip() or None

    if (
        normalized_discord_id is not None
        and participant_discord_id == normalized_discord_id
    ):
        return True
    if starter_pid is not None and participant.playerPid == starter_pid:
        return True
    return participant.playerName == starter_name


def _preserve_legacy_starter_pid(
    votes_for: tuple[VoteKickParticipantV1, ...],
    votes_against: tuple[VoteKickParticipantV1, ...],
    *,
    starter_name: str,
    starter_pid: int | None,
    starter_discord_id: str | None,
) -> tuple[tuple[VoteKickParticipantV1, ...], tuple[VoteKickParticipantV1, ...]]:
    if starter_pid is None:
        return votes_for, votes_against

    normalized_discord_id = str(starter_discord_id or "").strip() or None

    def patch_participants(
        participants: tuple[VoteKickParticipantV1, ...],
    ) -> tuple[tuple[VoteKickParticipantV1, ...], bool]:
        matched = False
        patched: list[VoteKickParticipantV1] = []
        for participant in participants:
            if not _vote_kick_participant_matches_starter(
                participant,
                starter_name=starter_name,
                starter_pid=starter_pid,
                starter_discord_id=normalized_discord_id,
            ):
                patched.append(participant)
                continue

            matched = True
            if participant.playerPid is not None:
                patched.append(participant)
                continue

            patched.append(
                VoteKickParticipantV1(
                    playerName=participant.playerName,
                    playerPid=starter_pid,
                    discordId=participant.discordId,
                )
            )

        return tuple(patched), matched

    patched_votes_for, matched_votes_for = patch_participants(votes_for)
    patched_votes_against, matched_votes_against = patch_participants(votes_against)
    if matched_votes_for or matched_votes_against:
        return patched_votes_for, patched_votes_against

    return (
        patched_votes_for
        + (
            VoteKickParticipantV1(
                playerName=starter_name,
                playerPid=starter_pid,
                discordId=normalized_discord_id,
            ),
        ),
        patched_votes_against,
    )


class _LegacyVoteKickPayload(_FrozenModel):
    target_name: str = Field(
        validation_alias=AliasChoices("targetName", "target_name", "target", "name")
    )
    target_pid: int | None = Field(
        default=None,
        validation_alias=AliasChoices("targetPid", "target_pid", "targetId", "pid"),
    )
    target_uuid: str | None = Field(
        default=None,
        validation_alias=AliasChoices("targetUuid", "target_uuid", "uuid"),
    )
    starter_name: str = Field(
        validation_alias=AliasChoices(
            "starterName",
            "starter_name",
            "starter",
            "initiatorName",
            "initiator_name",
            "adminName",
            "admin_name",
        )
    )
    starter_pid: int | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "starterPid",
            "starter_pid",
            "starterId",
            "initiatorPid",
            "initiator_pid",
            "adminPid",
            "admin_pid",
        ),
    )
    starter_discord_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "starterDiscordId",
            "starter_discord_id",
            "initiatorDiscordId",
            "initiator_discord_id",
            "adminDiscordId",
            "admin_discord_id",
        ),
    )
    reason: str
    votes_for: tuple[VoteKickParticipantV1, ...] = Field(
        default_factory=tuple,
        validation_alias=AliasChoices("votesFor", "votes_for", "yesVotes", "yes_votes"),
    )
    votes_against: tuple[VoteKickParticipantV1, ...] = Field(
        default_factory=tuple,
        validation_alias=AliasChoices(
            "votesAgainst",
            "votes_against",
            "noVotes",
            "no_votes",
        ),
    )

    @field_validator("target_name", "starter_name", "reason")
    @classmethod
    def _required_text_fields(cls, value: str) -> str:
        return cls._require_non_empty_text(value)

    @field_validator("target_pid", "starter_pid", mode="before")
    @classmethod
    def _optional_pid(cls, value: Any) -> int | None:
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        return _coerce_int(value)

    @field_validator("votes_for", "votes_against", mode="before")
    @classmethod
    def _default_participant_lists(
        cls, value: Any
    ) -> tuple[VoteKickParticipantV1, ...]:
        return _parse_vote_kick_participants(value)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "_LegacyVoteKickPayload":
        return cls._validate_payload(
            payload,
            error_message=(
                "Invalid vote-kick payload: expected target, starter, reason, and optional vote lists"
            ),
        )


def parse_ban_payload(payload: dict[str, Any]) -> ModerationBanCreatedV1:
    try:
        return ModerationBanCreatedV1.from_payload(payload)
    except (TypeError, ValueError):
        legacy = _LegacyBanPayload.from_payload(payload)
        return ModerationBanCreatedV1(
            target=_build_player_ref(
                uuid=legacy.uuid,
                pid=legacy.pid,
                ip=legacy.ip,
                name=legacy.name,
            ),
            actor=_build_actor_ref(
                name=legacy.admin_name,
                discord_id=legacy.admin_discord_id,
            ),
            reason=legacy.reason,
            expiration=_build_expiration_info(legacy.expire_date),
        )


def parse_mute_payload(payload: dict[str, Any]) -> ModerationMuteCreatedV1:
    try:
        return ModerationMuteCreatedV1.from_payload(payload)
    except (TypeError, ValueError):
        legacy = _LegacyMutePayload.from_payload(payload)
        return ModerationMuteCreatedV1(
            target=_build_player_ref(
                uuid=legacy.uuid,
                pid=legacy.pid,
                name=legacy.name,
            ),
            actor=_build_actor_ref(
                name=legacy.admin_name,
                discord_id=legacy.admin_discord_id,
            ),
            reason=legacy.reason,
            expiration=_build_expiration_info(legacy.expire_date),
        )


def parse_vote_kick_payload(payload: dict[str, Any]) -> ModerationVoteKickCreatedV1:
    try:
        return ModerationVoteKickCreatedV1.from_payload(payload)
    except (TypeError, ValueError):
        legacy = _LegacyVoteKickPayload.from_payload(payload)
        votes_for, votes_against = _preserve_legacy_starter_pid(
            legacy.votes_for,
            legacy.votes_against,
            starter_name=legacy.starter_name,
            starter_pid=legacy.starter_pid,
            starter_discord_id=legacy.starter_discord_id,
        )
        return ModerationVoteKickCreatedV1(
            target=_build_player_ref(
                uuid=legacy.target_uuid,
                pid=legacy.target_pid,
                name=legacy.target_name,
            ),
            actor=_build_actor_ref(
                name=legacy.starter_name,
                discord_id=legacy.starter_discord_id,
            ),
            reason=legacy.reason,
            votesFor=votes_for,
            votesAgainst=votes_against,
        )


class _LegacyGlobalChatPayload(_FrozenModel):
    author_name: str = Field(validation_alias=AliasChoices("authorName", "author_name"))
    message: str
    server: str

    @field_validator("author_name", "message", "server")
    @classmethod
    def _required_text(cls, value: str) -> str:
        return cls._require_non_empty_text(value)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "_LegacyGlobalChatPayload":
        return cls._validate_payload(
            payload,
            error_message="Invalid global chat payload: expected authorName, message, server",
        )


def parse_global_chat_payload(payload: dict[str, Any]) -> ChatGlobalV1:
    try:
        return ChatGlobalV1.from_payload(payload)
    except (TypeError, ValueError):
        legacy = _LegacyGlobalChatPayload.from_payload(payload)
        return ChatGlobalV1(
            authorName=legacy.author_name,
            message=legacy.message,
            server=legacy.server,
        )


class _LegacyDiscordLinkStatusPayload(_FrozenModel):
    player_uuid: str = Field(validation_alias=AliasChoices("playerUuid", "player_uuid"))
    player_pid: int = Field(validation_alias=AliasChoices("playerPid", "player_pid"))
    player_nickname: str = Field(
        validation_alias=AliasChoices(
            "playerNickname",
            "player_nickname",
            "playerName",
            "player_name",
        )
    )
    discord_id: str = Field(validation_alias=AliasChoices("discordId", "discord_id"))
    discord_username: str | None = Field(
        default=None,
        validation_alias=AliasChoices("discordUsername", "discord_username"),
    )
    action: str
    server: str
    occurred_at: int = Field(validation_alias=AliasChoices("occurredAt", "occurred_at"))

    @field_validator("player_uuid", "player_nickname", "discord_id", "action", "server")
    @classmethod
    def _required_text(cls, value: str) -> str:
        return cls._require_non_empty_text(value)

    @field_validator("player_pid", "occurred_at", mode="before")
    @classmethod
    def _parse_int_fields(cls, value: Any) -> int:
        return _coerce_int(value)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "_LegacyDiscordLinkStatusPayload":
        return cls._validate_payload(
            payload,
            error_message="Invalid discord link status payload",
        )


def parse_discord_link_status_payload(
    payload: dict[str, Any],
) -> DiscordLinkStatusChangedV1:
    try:
        return DiscordLinkStatusChangedV1.from_payload(payload)
    except (TypeError, ValueError):
        legacy = _LegacyDiscordLinkStatusPayload.from_payload(payload)
        try:
            action = DiscordLinkStatusChangedV1Action(legacy.action)
        except ValueError as error:
            raise ValueError("Invalid discord link status payload") from error

        return DiscordLinkStatusChangedV1(
            player=PlayerRefV1(
                playerUuid=legacy.player_uuid,
                playerPid=legacy.player_pid,
                playerName=legacy.player_nickname,
            ),
            discord=DiscordIdentityRefV1(
                discordId=legacy.discord_id,
                discordUsername=legacy.discord_username,
            ),
            action=action,
            server=legacy.server,
            occurredAt=_epoch_millis_to_iso8601(legacy.occurred_at),
        )


class DiscordAdminAccessChangedEvent(_FrozenModel):
    player_uuid: str = Field(validation_alias=AliasChoices("playerUuid", "player_uuid"))
    player_pid: int = Field(validation_alias=AliasChoices("playerPid", "player_pid"))
    discord_id: str = Field(validation_alias=AliasChoices("discordId", "discord_id"))
    discord_username: str | None = Field(
        default=None,
        validation_alias=AliasChoices("discordUsername", "discord_username"),
    )
    admin: bool
    admin_source: str = Field(
        validation_alias=AliasChoices("adminSource", "admin_source")
    )
    requested_by: str = Field(
        validation_alias=AliasChoices("requestedBy", "requested_by")
    )
    reason: str
    server: str
    occurred_at: int = Field(validation_alias=AliasChoices("occurredAt", "occurred_at"))

    @field_validator(
        "player_uuid", "discord_id", "admin_source", "requested_by", "reason", "server"
    )
    @classmethod
    def _required_text(cls, value: str) -> str:
        return cls._require_non_empty_text(value)

    @field_validator("player_pid", "occurred_at", mode="before")
    @classmethod
    def _parse_int_fields(cls, value: Any) -> int:
        return _coerce_int(value)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "DiscordAdminAccessChangedEvent":
        return cls._validate_payload(
            payload,
            error_message="Invalid discord admin access payload",
        )


class _LegacyServerHeartbeatPayload(_FrozenModel):
    server_name: str = Field(validation_alias=AliasChoices("serverName", "server_name"))
    discord_channel_id: int = Field(
        validation_alias=AliasChoices("discordChannelId", "discord_channel_id")
    )
    players: int
    max_players: int = Field(validation_alias=AliasChoices("maxPlayers", "max_players"))
    version: str
    host: str | None = Field(
        default=None, validation_alias=AliasChoices("host", "serverHost", "server_host")
    )
    port: int | None = Field(
        default=None, validation_alias=AliasChoices("port", "serverPort", "server_port")
    )

    @field_validator("server_name", "version")
    @classmethod
    def _required_text(cls, value: str) -> str:
        return cls._require_non_empty_text(value)

    @field_validator("discord_channel_id", "players", "max_players", mode="before")
    @classmethod
    def _parse_int_fields(cls, value: Any) -> int:
        return _coerce_int(value)

    @field_validator("host", mode="before")
    @classmethod
    def _parse_host(cls, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            normalized = value.strip()
            return normalized if normalized else None
        return str(value)

    @field_validator("port", mode="before")
    @classmethod
    def _parse_optional_port(cls, value: Any) -> int | None:
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        return _coerce_int(value)


def parse_server_heartbeat_payload(payload: dict[str, Any]) -> ServerHeartbeatV1:
    try:
        return ServerHeartbeatV1.from_payload(payload)
    except (TypeError, ValueError):
        legacy = _LegacyServerHeartbeatPayload._validate_payload(
            payload,
            error_message=(
                "Invalid heartbeat payload: expected canonical server.heartbeat payload or legacy serverName, discordChannelId, players, maxPlayers, version"
            ),
        )
        return ServerHeartbeatV1(
            serverName=legacy.server_name,
            discordChannelId=legacy.discord_channel_id,
            players=legacy.players,
            maxPlayers=legacy.max_players,
            version=legacy.version,
            host=legacy.host,
            port=legacy.port,
        )


class RawEvent(_FrozenModel):
    event_type: str
    payload: dict[str, Any]

    @classmethod
    def from_fields(cls, fields: dict[str, Any]) -> "RawEvent":
        event_type_raw = fields.get("event_type")
        if not isinstance(event_type_raw, str) or not event_type_raw:
            raise ValueError("Invalid raw event fields: expected event_type")

        payload_raw = fields.get("payload_json", "{}")
        if not isinstance(payload_raw, str):
            payload_raw = str(payload_raw)

        try:
            payload = loads(payload_raw)
        except Exception as error:
            raise ValueError(
                "Invalid raw event fields: payload_json is not valid JSON"
            ) from error

        if not isinstance(payload, dict):
            raise ValueError(
                "Invalid raw event fields: payload_json must decode to object"
            )

        return cls(event_type=event_type_raw, payload=payload)


__all__ = [
    "ChatGlobalV1",
    "ChatMessageV1",
    "DiscordAdminAccessChangedEvent",
    "DiscordLinkStatusChangedV1",
    "EventType",
    "LEGACY_HEARTBEAT_EVENT_TYPES",
    "ModerationBanCreatedV1",
    "ModerationMuteCreatedV1",
    "ModerationVoteKickCreatedV1",
    "parse_chat_message_payload",
    "parse_ban_payload",
    "parse_discord_link_status_payload",
    "parse_global_chat_payload",
    "parse_mute_payload",
    "parse_player_join_leave_payload",
    "parse_server_action_payload",
    "parse_server_heartbeat_payload",
    "parse_vote_kick_payload",
    "PlayerJoinLeaveV1",
    "RawEvent",
    "ServerActionV1",
    "ServerHeartbeatV1",
    "VoteKickParticipant",
]
