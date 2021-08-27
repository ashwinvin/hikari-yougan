from __future__ import annotations

import typing

import aiohttp
from yougan.node import Node
from yougan.player import Player


if typing.TYPE_CHECKING:
    from hikari import channels
    from hikari import guilds
    from hikari import snowflakes
    from hikari import traits
    from yougan import models

    _PT = typing.TypeVar("_PT", bound=Player)

__all__: typing.Tuple[str, ...] = ("Client",)


class Client:
    def __init__(self, app: traits.BotAware) -> None:
        self.app = app
        self.nodes: typing.Mapping[str, Node] = {}
        self.session = None
        self.players: typing.Mapping[snowflakes.Snowflake, _PT] = {}

    @property
    def is_connected(self) -> bool:
        """Check if there is any active connection to the nodes"""
        for node in self.nodes.values():
            if node.is_connected:
                return True
        return False

    async def close(self) -> None:
        for node in self.nodes.values():
            await node.disconnect()

    def get_best_node(self):
        return sorted(self.nodes.values(), key=lambda node: len(node.players))[0]

    def get_player(self, guild_id: snowflakes.Snowflakeish[guilds.Guild]) -> typing.Optional[Player]:
        try:
            return self.players[int(guild_id)]
        except KeyError:
            return None

    async def connect(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.Guild],
        channel: snowflakes.SnowflakeishOr[channels.GuildVoiceChannel],
        *,
        deaf: bool = False,
        mute: bool = False,
        node: typing.Optional[Node] = None,
        cls: typing.Optional[typing.Type[_PT]] = Player,
        **kwargs: typing.Any,
    ) -> Player:

        if not issubclass(cls, Player):
            raise TypeError(f"Expected cls to derived from Player but got {type(cls)}")

        if not node:
            node: Node = self.get_best_node()

        if node not in self.nodes.values():
            raise Exception("Unknown Node Provided")
            
        self.players[int(guild)] = await self.app.voice.connect_to(
            guild, channel, cls, deaf=deaf, mute=mute, node=node, **kwargs
        )
        node.players[int(guild)] = self.players[int(guild)]
        return self.players[int(guild)]

    async def disconnect(self) -> None:
        for connection in self.players.values():
            await connection.destroy()  # Is this really required?

        for node in self.nodes.values():
            await node.destroy()

    def add_node(self, *, name, host, port, password) -> None:
        self.nodes[name] = Node(name=name, host=host, port=port, password=password, app=self.app)

    async def remove_node(self, name: str) -> None:
        if self.nodes[name].is_connected:
            await self.nodes[name].destroy()
        del self.nodes[name]

    async def start_nodes(self) -> None:
        if not self.session:
            self.session = aiohttp.ClientSession()

        for node in self.nodes.values():
            await node.start(self.session)

    async def search_track(
        self,
        query: str,
        *,
        yt: typing.Optional[bool] = False,
        sc: typing.Optional[bool] = False,
    ) -> typing.Union[models.SearchResult, models.YTPlaylist, models.Track]:
        node = self.get_best_node()
        return await node.search_tracks(query, yt=yt, sc=sc)

    async def fetch_track(self, track_id: str) -> models.Track:
        node = self.get_best_node()
        return await node.fetch_track(track_id)
