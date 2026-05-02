from __future__ import annotations

from xcore_protocol.generated.discord import DiscordLinkStatusChangedV1Action
from xcore_protocol.generated.shared import DiscordIdentityRefV1, PlayerRefV1

from xcore_discord_bot.contracts import (
    ChatGlobalV1,
    ChatMessageV1,
    DiscordLinkStatusChangedV1,
    EventType,
    ModerationBanCreatedV1,
    ModerationMuteCreatedV1,
    ModerationVoteKickCreatedV1,
    parse_chat_message_payload,
    parse_ban_payload,
    parse_discord_link_status_payload,
    parse_global_chat_payload,
    parse_mute_payload,
    parse_player_join_leave_payload,
    parse_server_action_payload,
    parse_vote_kick_payload,
    PlayerJoinLeaveV1,
    RawEvent,
    ServerHeartbeatV1,
    ServerActionV1,
    VoteKickParticipant,
    parse_server_heartbeat_payload,
)


def test_game_chat_message_from_payload() -> None:
    payload = {
        "messageType": "chat.message",
        "messageVersion": 1,
        "authorName": "pizduk",
        "message": "yyyy",
        "server": "mini-pvp",
    }
    event = parse_chat_message_payload(payload)
    assert isinstance(event, ChatMessageV1)
    assert event.authorName == "pizduk"
    assert event.message == "yyyy"
    assert event.server == "mini-pvp"


def test_player_join_leave_from_payload() -> None:
    payload = {
        "messageType": "player.join-leave",
        "messageVersion": 1,
        "playerName": "pizduk",
        "server": "mini-pvp",
        "joined": True,
    }
    event = parse_player_join_leave_payload(payload)
    assert isinstance(event, PlayerJoinLeaveV1)
    assert event.playerName == "pizduk"
    assert event.server == "mini-pvp"
    assert event.joined is True


def test_server_action_from_payload() -> None:
    payload = {
        "messageType": "server.action",
        "messageVersion": 1,
        "message": "Server started",
        "server": "mini-pvp",
    }
    event = parse_server_action_payload(payload)
    assert isinstance(event, ServerActionV1)
    assert event.message == "Server started"
    assert event.server == "mini-pvp"


def test_player_join_leave_payload_falls_back_to_legacy_join_shape() -> None:
    payload = {"playerName": "legacy", "server": "mini-pvp", "join": True}

    event = parse_player_join_leave_payload(payload)

    assert event == PlayerJoinLeaveV1(
        playerName="legacy",
        server="mini-pvp",
        joined=True,
    )


def test_server_action_payload_falls_back_to_legacy_shape() -> None:
    payload = {"message": "Server started", "server": "mini-pvp"}

    event = parse_server_action_payload(payload)

    assert event == ServerActionV1(
        message="Server started",
        server="mini-pvp",
    )


def test_ban_payload_from_legacy_snake_case() -> None:
    payload = {
        "pid": "7",
        "uuid": "u-1",
        "ip": "1.2.3.4",
        "name": "pizduk",
        "admin_name": "admin",
        "admin_discord_id": "123",
        "reason": "rule",
        "expire_date": "2026-03-01T10:00:00+00:00",
    }
    event = parse_ban_payload(payload)
    assert isinstance(event, ModerationBanCreatedV1)
    assert event.target.playerPid == 7
    assert event.target.playerUuid == "u-1"
    assert event.target.ip == "1.2.3.4"
    assert event.target.playerName == "pizduk"
    assert event.actor.actorName == "admin"
    assert event.actor.actorDiscordId == "123"
    assert event.reason == "rule"
    assert event.expiration is not None
    assert event.expiration.expiresAt == "2026-03-01T10:00:00+00:00"


def test_ban_payload_from_canonical_generated_shape() -> None:
    payload = {
        "messageType": "moderation.ban.created",
        "messageVersion": 1,
        "target": {"playerUuid": "u-2", "playerPid": 12, "playerName": "player"},
        "actor": {"actorName": "mod", "actorDiscordId": "555"},
        "reason": "abuse",
        "expiration": {"expiresAt": "2026-03-01T11:00:00+00:00", "permanent": False},
    }
    event = parse_ban_payload(payload)
    assert event.target.playerPid == 12
    assert event.actor.actorName == "mod"
    assert event.actor.actorDiscordId == "555"
    assert event.expiration is not None
    assert event.expiration.expiresAt == "2026-03-01T11:00:00+00:00"


def test_mute_payload_from_legacy_camel_case_admin_and_expire() -> None:
    payload = {
        "playerPid": 12,
        "uuid": "u-2",
        "name": "player",
        "adminName": "mod",
        "adminDiscordId": "777",
        "reason": "spam",
        "expireDate": "2026-03-01T11:00:00+00:00",
    }
    event = parse_mute_payload(payload)
    assert isinstance(event, ModerationMuteCreatedV1)
    assert event.target.playerPid == 12
    assert event.target.playerUuid == "u-2"
    assert event.actor.actorName == "mod"
    assert event.actor.actorDiscordId == "777"
    assert event.reason == "spam"
    assert event.expiration is not None
    assert event.expiration.expiresAt == "2026-03-01T11:00:00+00:00"


def test_global_chat_event_from_payload() -> None:
    payload = {
        "messageType": "chat.global",
        "messageVersion": 1,
        "authorName": "pizduk",
        "message": "hello all",
        "server": "mini-pvp",
    }
    event = parse_global_chat_payload(payload)
    assert isinstance(event, ChatGlobalV1)
    assert event.authorName == "pizduk"
    assert event.message == "hello all"
    assert event.server == "mini-pvp"


def test_chat_message_payload_falls_back_to_legacy_shape() -> None:
    payload = {"authorName": "legacy", "message": "hello", "server": "mini-pvp"}

    event = parse_chat_message_payload(payload)

    assert event == ChatMessageV1(
        authorName="legacy",
        message="hello",
        server="mini-pvp",
    )


def test_global_chat_payload_falls_back_to_legacy_shape() -> None:
    payload = {"authorName": "legacy", "message": "hello all", "server": "mini-pvp"}

    event = parse_global_chat_payload(payload)

    assert event == ChatGlobalV1(
        authorName="legacy",
        message="hello all",
        server="mini-pvp",
    )


def test_vote_kick_payload_from_legacy_shape_with_votes() -> None:
    payload = {
        "targetName": "Target",
        "targetPid": "42",
        "targetUuid": "uuid-target",
        "starterName": "Starter",
        "starterPid": "7",
        "starterDiscordId": "123456",
        "reason": "griefing",
        "votesFor": [
            {"playerName": "Starter", "playerPid": "7", "discordId": "123456"}
        ],
        "votesAgainst": [
            {"playerName": "Voter2", "playerPid": 8, "discordId": "654321"}
        ],
    }
    event = parse_vote_kick_payload(payload)
    assert isinstance(event, ModerationVoteKickCreatedV1)
    assert event.target.playerName == "Target"
    assert event.target.playerPid == 42
    assert event.target.playerUuid == "uuid-target"
    assert event.actor.actorName == "Starter"
    assert event.actor.actorDiscordId == "123456"
    assert event.reason == "griefing"
    assert event.votesFor is not None
    assert event.votesFor[0].discordId == "123456"
    assert event.votesAgainst is not None
    assert event.votesAgainst[0].playerName == "Voter2"


def test_vote_kick_payload_preserves_legacy_target_without_uuid() -> None:
    payload = {
        "target": "Target",
        "targetId": "42",
        "starter": "Starter",
        "adminDiscordId": "123456",
        "reason": "griefing",
        "votesFor": [{"playerName": "Starter", "playerPid": 7, "discordId": "123456"}],
        "votesAgainst": [],
    }

    event = parse_vote_kick_payload(payload)

    assert event.target.playerName == "Target"
    assert event.target.playerPid == 42
    assert event.target.playerUuid == "legacy:Target"
    assert event.actor.actorName == "Starter"
    assert event.actor.actorDiscordId == "123456"


def test_vote_kick_participant_adapter_still_accepts_legacy_aliases() -> None:
    participant = VoteKickParticipant.model_validate(
        {"nickname": "Starter", "playerPid": "7", "discordId": "123456"}
    )

    assert participant.name == "Starter"
    assert participant.pid == 7
    assert participant.discord_id == "123456"


def test_raw_event_from_fields() -> None:
    fields = {
        "event_type": "event.someunknown",
        "payload_json": '{"a":1,"b":"x"}',
    }
    event = RawEvent.from_fields(fields)
    assert event.event_type == "event.someunknown"
    assert event.payload == {"a": 1, "b": "x"}


def test_server_heartbeat_from_payload() -> None:
    payload = {
        "messageType": "server.heartbeat",
        "messageVersion": 1,
        "serverName": "mini-pvp",
        "discordChannelId": 1234,
        "players": 4,
        "maxPlayers": 10,
        "version": "1.2.3",
    }
    event = parse_server_heartbeat_payload(payload)
    assert isinstance(event, ServerHeartbeatV1)
    assert event.serverName == "mini-pvp"
    assert event.discordChannelId == 1234
    assert event.players == 4
    assert event.maxPlayers == 10
    assert event.version == "1.2.3"


def test_server_heartbeat_from_payload_with_address_aliases() -> None:
    payload = {
        "serverName": "mini-pvp",
        "discordChannelId": "1234",
        "players": 4,
        "maxPlayers": 10,
        "version": "1.2.3",
        "serverHost": "play.example.com",
        "serverPort": "6567",
    }
    event = parse_server_heartbeat_payload(payload)
    assert event.host == "play.example.com"
    assert event.port == 6567


def test_heartbeat_event_type_literal() -> None:
    assert EventType.HEARTBEAT == "ServerHeartbeatEvent"


def test_discord_link_status_changed_from_payload() -> None:
    payload = {
        "messageType": "discord.link.status-changed",
        "messageVersion": 1,
        "player": {"playerUuid": "uuid-7", "playerPid": 7, "playerName": "Target"},
        "discord": {"discordId": "123456", "discordUsername": "osp54"},
        "action": "linked",
        "server": "mini-pvp",
        "occurredAt": "2026-05-02T10:20:30.123+00:00",
    }
    event = parse_discord_link_status_payload(payload)
    assert isinstance(event, DiscordLinkStatusChangedV1)
    assert event.player.playerUuid == "uuid-7"
    assert event.player.playerPid == 7
    assert event.player.playerName == "Target"
    assert event.discord.discordId == "123456"
    assert event.discord.discordUsername == "osp54"
    assert str(event.action) == "linked"
    assert event.server == "mini-pvp"
    assert event.occurredAt == "2026-05-02T10:20:30.123+00:00"


def test_discord_link_status_changed_from_legacy_flat_payload() -> None:
    payload = {
        "playerUuid": "uuid-7",
        "playerPid": "7",
        "playerNickname": "Target",
        "discordId": "123456",
        "discordUsername": "osp54",
        "action": "linked",
        "server": "mini-pvp",
        "occurredAt": "123456789",
    }

    event = parse_discord_link_status_payload(payload)

    assert event == DiscordLinkStatusChangedV1(
        player=PlayerRefV1(playerUuid="uuid-7", playerPid=7, playerName="Target"),
        discord=DiscordIdentityRefV1(
            discordId="123456",
            discordUsername="osp54",
        ),
        action=DiscordLinkStatusChangedV1Action.LINKED,
        server="mini-pvp",
        occurredAt="1970-01-02T10:17:36.789+00:00",
    )
