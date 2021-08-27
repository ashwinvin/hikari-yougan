from __future__ import annotations

import logging
import typing

from yougan.connection import Connection
from yougan import stats
from yougan import models

if typing.TYPE_CHECKING:
    import aiohttp
    from hikari import guilds
    from hikari import snowflakes
    from hikari import traits

    from yougan.player import Player

__all__: typing.Tuple[str, ...] = ("Node",)
_LOGGER = logging.getLogger("yougan")


class Node:
    def __init__(
        self,
        *,
        name: str,
        host: str,
        port: int,
        password: str,
        app: traits.BotAware,
        session: aiohttp.ClientSession = None,
    ) -> None:
        self.name = name
        self.host = host
        self.port = port
        self.password = password
        self.app = app
        self.session: aiohttp.ClientSession = session
        self.connection: Connection = None
        self.is_connected = False
        self.stats = stats.Stats()
        self.players: typing.Mapping[snowflakes.SnowflakeishOr[guilds.Guild], Player] = {}

    @property
    def headers(self):
        return {"Authorization": self.password, "Accept": "application/json"}

    def get_player(self, guild: snowflakes.Snowflakeish[guilds.Guild]) -> typing.Optional[Player]:
        try:
            return self.players[int(guild)]
        except KeyError:
            return None

    async def search_tracks(
        self,
        query: str,
        *,
        yt: typing.Optional[bool] = False,
        sc: typing.Optional[bool] = False,
    ) -> typing.Union[models.SearchResult, models.YTPlaylist, models.Track]:
        """Search and return track(s) for the given query.

        Parameters
        ----------
        query : str
            The query to search for track(s). This must be a valid URL.

        Other Parameters
        ----------------
        yt: typing.Optional[builtins.bool]
            Searches the given query in Youtube.

            This is false by default.

        sc: typing.Optional[builtins.bool]
            Searches the given query in Sound Cloud.

            This is false by default.

        Returns
        -------
        typing.Union[yougan.models.SearchResult, yougan.models.YTPlaylist, yougan.models.Track]
            Returns the result of the query.

        """
        _LOGGER.debug("Querying for %s in Node::%s", query, self.name)

        if yt:
            query = f"ytsearch:{query}"
        elif sc:
            query = f"scsearch:{query}"

        params = {"identifier": query}

        async with self.session.get(
            f"http://{self.host}:{self.port}/loadtracks",
            headers=self.headers,
            params=params,
        ) as resp:
            payload = await resp.json()
            if payload.get("error", None):
                raise models.TrackLoadError(f"{payload['error']}: {payload['message']}")

            if payload["loadType"] == "SEARCH_RESULT":
                tracks = [models.Track.from_dict(track) for track in payload["tracks"]]
                return models.SearchResult(tracks=tracks, query=query)

            elif payload["loadType"] == "TRACK_LOADED":
                return models.Track.from_dict(payload["tracks"][0])

            elif payload["loadType"] == "PLAYLIST_LOADED":
                tracks = [models.Track.from_dict(track) for track in payload["tracks"]]
                info = payload["playlistInfo"]
                return models.YTPlaylist(
                    name=info["name"],
                    tracks=tracks,
                    selected_track=info["selectedTrack"],
                )

            elif payload["loadType"] == "LOAD_FAILED":
                exception = payload["exception"]
                raise models.TrackLoadError(f'{exception["severity"]}: {exception["message"]}')

    async def fetch_track(self, track_id: str) -> models.Track:
        params = {"track": track_id}
        async with self.session.get(
            f"http://{self.host}:{self.port}/decodetrack",
            headers=self.headers,
            params=params,
        ) as resp:
            payload = await resp.json()
            payload = {"track": track_id, "info": payload}
            return models.Track.from_dict(payload)

    async def start(self, session: typing.Optional[aiohttp.ClientSession]) -> None:
        """Connects to the lavalink server using the given credentials."""
        _LOGGER.info("Attempting to connect to Node::%s", self.name)

        self.session = session
        if not self.session:
            self.session = session

        self.connection = Connection(host=self.host, port=self.port, password=self.password, node=self)
        await self.connection.connect_node()
        self.is_connected = True

    async def connect_vc(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.Guild],
        session_id: str,
        token: str,
        endpoint: str,
    ) -> None:
        if not self.is_connected:
            raise Exception("Node is not connected yet!")
        await self.connection.connect_vc(session_id, guild, token, endpoint)

    async def _send(self, payload: typing.Dict[str, typing.Any]) -> None:
        if not self.is_connected:
            raise Exception("Node is not connected yet!")
        await self.connection.send(payload)

    async def destroy(self) -> None:
        """Closes the connection to the lavalink server."""
        _LOGGER.info("Disconnecting from Node::%s", self.name)
        await self.connection.close()
        self.is_connected = False
