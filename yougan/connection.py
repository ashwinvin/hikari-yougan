from __future__ import annotations

import asyncio
import logging
import typing
import json

import aiohttp

from yougan import events
from yougan import errors

if typing.TYPE_CHECKING:
    from yougan.node import Node


__all__: typing.Tuple[str, ...] = ("Connection",)

_LOGGER = logging.getLogger("yougan-websocket")


class Connection:
    def __init__(
        self,
        *,
        host: str,
        port: int,
        password: str,
        node: Node,
    ) -> None:
        self._conn = None
        self.host = host
        self.port = port
        self.password = password
        self.session = node.session
        self.app = node.app
        self.is_connected = False
        self._listener = None
        self.node = node

    @property
    def headers(self):
        return {
            "Authorization": self.password,
            "Num-shards": str(self.app.shard_count),
            "User-Id": str(self.app.get_me().id),
        }

    async def connect_node(self):
        if self.is_connected:
            raise errors.NodeAlreadyConnect(self.node.name)

        try:
            self._conn = await self.session.ws_connect(f"ws://{self.host}:{self.port}", headers=self.headers)
        except aiohttp.WSServerHandshakeError:
            raise errors.AuthenticationError(f"Node::{self.node.name} Authentication Failed!")

        self.is_connected = True
        loop = asyncio.get_event_loop()
        loop.create_task(self._listen(), name=f"Lavalink voice listener for Node::{self.node.name}")

    async def connect_vc(self, session_id, guild_id, token, endpoint) -> None:
        if not self.is_connected:
            raise Exception(f"Node::{self.node.name} is not connected!!")
        _LOGGER.debug("Connecting to voice in guild %s using Node::%s", guild_id, self.node.name)

        await self.send(
            {
                "op": "voiceUpdate",
                "sessionId": session_id,
                "guildId": str(guild_id),
                "event": {
                    "token": token,
                    "guild_id": str(guild_id),
                    "endpoint": endpoint,
                },
            }
        )

    async def _listen(self) -> None:
        while True:
            msg = await self._conn.receive()
            msg = msg.json()
            _LOGGER.debug("Receiving from %s with packet %s", self.host, msg)

            if msg["op"] == "stats":
                self.node.stats.update(msg)

            if msg["op"] == "event":
                event = self.deserialise_track_events(msg)
                if not event:
                    return
                self.node.app.dispatch(event)

            if msg["op"] == "playerUpdate":
                player = self.node.get_player(msg["guildId"])
                player._update_state(position=msg["state"]["position"], length=msg["state"]["time"])

            else:
                _LOGGER.warning("Unknown op %s recieved from Node::%s", msg["op"], self.node.name)

    def deserialise_track_events(self, payload: typing.Dict[str, str]):
        player = self.node.get_player(int(payload["guildId"]))

        if payload["type"] == "TrackStartEvent":
            return events.TrackStartEvent(app=self.app, track=payload["track"], player=player)

        elif payload["type"] == "TrackEndEvent":
            return events.TrackEndEvent(app=self.app, track=payload["track"], reason=payload["reason"], player=player)

        elif payload["type"] == "TrackStuckEvent":
            return events.TrackStuckEvent(
                app=self.app, track=payload["track"], thershold=payload["thresholdMs"], player=player
            )

        elif payload["type"] == "TrackExceptionEvent":
            return events.TrackExceptionEvent(
                app=self.app, track=payload["track"], error=payload["error"], player=player
            )

    async def send(self, payload) -> None:
        _LOGGER.debug("Sending %s with packet %s", self.host, payload)
        jpayload = json.dumps(payload)
        await self._conn.send_str(jpayload)

    async def close(self) -> None:
        if not self.is_connected:
            return
        await self.websocket.close(code=1006)
