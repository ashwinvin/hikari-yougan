from __future__ import annotations
import logging

import typing

from hikari import events

from yougan.models import Track

if typing.TYPE_CHECKING:
    from hikari import snowflakes
    from hikari.impl import voice

    from yougan.node import Node

    _T = typing.TypeVar("_T")

__all__: typing.Tuple[str, ...] = ("Player",)


class Player:
    def __init__(
        self,
        node: Node,
        owner: voice.VoiceComponentImpl,
        guild_id: snowflakes.Snowflake,
        channel_id: snowflakes.Snowflake,
        user_id: snowflakes.Snowflake,
        session_id: str,
        token: str,
        endpoint: str,
        shard_id: int,
        on_close: typing.Callable[[_T], typing.Awaitable[None]],
    ) -> None:
        self.node = node
        self.guild_id = guild_id
        self.channel_id = channel_id

        self.user_id = user_id
        self._token = token
        self._endpoint = endpoint
        self._session_id = session_id
        self._owner = owner
        self._on_close = on_close
        self.shard_id = shard_id

        self.is_paused: bool = False
        self.is_stopped: bool = False
        self.volume: int = 100
        self.is_connected: bool = False
        self.current_track = None

    @property
    def is_playing(self):
        return self.is_connected and self.current_track

    async def play(self, track: Track, replace: bool = False) -> None:
        if not isinstance(track, Track):
            raise TypeError(f"Expected arg track to be of type 'Track' but recieved '{type(track)}'")

        await self.node._send(
            {
                "op": "play",
                "guildId": str(self.guild_id),
                "track": track.id,
                "noReplace": not replace,
            }
        )

        self.current_track = track

    async def _connect(self) -> None:
        await self.node.connect_vc(self.guild_id, self._session_id, self._token, self._endpoint)
        self.is_connected = True

    async def stop(self) -> None:
        await self.node._send({"op": "stop", "guildId": str(self.guild_id)})
        self.is_stopped = True

    async def pause(self) -> None:
        await self.node._send({"op": "pause", "guildId": str(self.guild_id), "pause": True})
        self.is_paused = True

    async def disconnect(self) -> None:
        await self.node._send({"op": "destroy", "guildId": str(self.guild_id)})
        del self.node.players[self.guild_id]
        await self._on_close(self)

    async def resume(self) -> None:
        await self.node._send({"op": "pause", "guildId": str(self.guild_id), "pause": False})
        self.is_paused = False

    async def set_volume(self, volume: int) -> None:
        await self.node._send({"op": "volume", "guildId": str(self.guild_id), "volume": volume})
        self.volume = volume

    async def notify(self, event: events.VoiceEvent) -> None:
        """Called when a voice update happens in the connected channel"""

        logging.debug("Ignoring voice event %s", event)

    def _update_state(self, *, position: int = 0, length: int):
        self.current_track.position = position
        self.current_track.length = length

    @classmethod
    async def initialize(
        cls,
        *,
        channel_id: snowflakes.Snowflake,
        endpoint: str,
        guild_id: snowflakes.Snowflake,
        on_close: typing.Callable[[_T], typing.Awaitable[None]],
        owner: _T,
        session_id: str,
        shard_id: int,
        token: str,
        user_id: snowflakes.Snowflake,
        node,
    ):
        cls = cls(
            channel_id=channel_id,
            guild_id=guild_id,
            endpoint=endpoint[6:],  # Stripping "wss://". THANKS DAVFSA !!!!!
            session_id=session_id,
            token=token,
            node=node,
            shard_id=shard_id,
            owner=owner,
            on_close=on_close,
            user_id=user_id,
        )
        await cls._connect()

        return cls
