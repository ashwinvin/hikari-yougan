from __future__ import annotations
from email.policy import default
import logging

import typing

from dataclasses import dataclass

from hikari import events
from hikari.api import VoiceConnection, VoiceComponent

from yougan.models import Track

if typing.TYPE_CHECKING:
    from hikari import snowflakes

    from yougan.node import Node

    _T = typing.TypeVar("_T")

__all__: typing.Tuple[str, ...] = ("Player",)


@dataclass
class Player(VoiceConnection):
    node: Node

    _user_id: snowflakes.Snowflake
    _token: str
    _endpoint: str
    _session_id: str
    _owner: VoiceComponent
    _on_close: typing.Callable[[_T], typing.Awaitable[None]]
    _shard_id: int
    _guild_id: snowflakes.Snowflake
    _channel_id: snowflakes.Snowflake

    _current_track: typing.Optional[Track] = None
    _is_alive: bool = True
    is_stopped: bool = True
    is_paused: bool = False
    volume: int = 100

    @property
    def channel_id(self) -> snowflakes.Snowflake:
        """Return the ID of the voice channel this voice connection is in.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The channel id.
        """
        return self._channel_id

    @property
    def guild_id(self) -> snowflakes.Snowflake:
        """Return the ID of the guild this voice connection is in.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The guild id.
        """
        return self._guild_id

    @property
    def is_alive(self) -> bool:
        """Return `builtins.True` if the connection is alive.

        Returns
        -------
        bool
            The connection state.
        """
        return self._is_alive

    @property
    def shard_id(self) -> int:
        """Return the ID of the shard that requested the connection.

        Returns
        -------
        int
            The shard id.
        """
        return self._shard_id

    @property
    def owner(self) -> VoiceComponent:
        """Return the component that is managing this connection."""
        return self._owner

    @property
    def current_track(self) -> typing.Optional[Track]:
        """Return the current playing track."""
        return self._current_track

    @property
    def is_playing(self) -> bool:
        """Return `builtins.True` if the player is currently playing a track

        Returns
        -------
        bool
            The player state.
        """
        return self.is_alive and self.current_track is not None

    async def join(self) -> None:
        """Wait for the process to halt before continuing."""

    async def _connect(self) -> None:
        await self.node.connect_vc(self.guild_id, self._session_id, self._token, self._endpoint)
        self.is_connected = True

    async def play(self, track: Track, replace: bool = False) -> None:
        """Plays the given track in the voice channel.

        Parameters
        ----------
        track : yougan.models.Track
            The track to play
        replace: builtins.bool
            If true, the requested track will replace the current playing track.
        """
        if not isinstance(track, Track):
            raise TypeError(f"Expected arg track to be a subclass of 'Track' but recieved '{type(track)}'")

        await self.node._send(
            {
                "op": "play",
                "guildId": str(self.guild_id),
                "track": track.id,
                "noReplace": not replace,
            }
        )

        self._current_track = track

    async def stop(self) -> None:
        """Stop the current playing track."""
        await self.node._send({"op": "stop", "guildId": str(self.guild_id)})
        self.is_stopped = True

    async def pause(self) -> None:
        """Pause the current playing track."""
        await self.node._send({"op": "pause", "guildId": str(self.guild_id), "pause": True})
        self.is_paused = True

    async def disconnect(self) -> None:
        """Destroy and disconnect the player from the voice channel."""
        await self.node._send({"op": "destroy", "guildId": str(self.guild_id)})
        del self.node.players[self.guild_id]
        await self._on_close(self)

    async def resume(self) -> None:
        """Resume the current playing track if it was paused."""
        await self.node._send({"op": "pause", "guildId": str(self.guild_id), "pause": False})
        self.is_paused = False

    async def set_volume(self, volume: int) -> None:
        """Set the volume of the current player.
        Parameters
        ----------
        volume: int
            The volume to set for the player.
        """
        await self.node._send({"op": "volume", "guildId": str(self.guild_id), "volume": volume})
        self.volume = volume

    async def notify(self, event: events.VoiceEvent) -> None:
        """Called when a voice update happens in the connected channel"""
        logging.debug("Ignoring voice event %s", event)

    def _update_state(self, *, position: int = 0, length: int) -> None:
        if not self._current_track:
            return
        self._current_track.position = position
        self._current_track.length = length

    @classmethod
    async def initialize(
        cls,
        channel_id: snowflakes.Snowflake,
        endpoint: str,
        guild_id: snowflakes.Snowflake,
        on_close: typing.Callable[[_T], typing.Awaitable[None]],
        owner: VoiceComponent,
        session_id: str,
        shard_id: int,
        token: str,
        user_id: snowflakes.Snowflake,
        **kwargs: typing.Any,
    ) -> Player:
        """Initialize and connect the voice connection.

        Parameters
        ----------
        channel_id : hikari.snowflakes.Snowflake
            The channel ID that the voice connection is actively connected to.
        endpoint : str
            The voice websocket endpoint to connect to. Will contain the
            protocol at the start (i.e. `wss://`), and end with the **correct**
            port (the port and protocol are sanitized since Discord still
            provide the wrong information four years later).
        guild_id : hikari.snowflakes.Snowflake
            The guild ID that the websocket should connect to.
        on_close : typing.Callable[[T], typing.Awaitable[None]]
            A shutdown hook to invoke when closing a connection to ensure the
            connection is unregistered from the voice component safely.
        owner : VoiceComponent
            The component that made this connection object.
        session_id : builtins.str
            The voice session ID to use.
        shard_id : builtins.int
            The associated shard ID that the voice connection was generated
            from.
        token : builtins.str
            The voice token to use.
        user_id : hikari.snowflakes.Snowflake
            The user ID of the account that just joined the voice channel.
        **kwargs : typing.Any
            Any implementation-specific arguments to provide to the
            voice connection that is being initialized.

        Returns
        -------
        yougan.player.Player
            The type of this connection object.
        """
        if node := kwargs.get("node"):
            if not isinstance(node, Node):
                raise TypeError(f"Expected 'node' to be of type 'Node' but got type '{type(node)}'")
        else:
            raise KeyError("Missing node parameter")

        cls = cls(
            _channel_id=channel_id,
            _endpoint=endpoint,
            _guild_id=guild_id,
            _on_close=on_close,
            _owner=owner,
            _session_id=session_id,
            _shard_id=shard_id,
            _token=token,
            _user_id=user_id,
            node=node,
        )
        await cls._connect()
        return cls
