import typing

__all__: typing.Tuple[str, ...] = ("Track", "SearchResult", "YTPlaylist")


class Track:
    def __init__(
        self,
        id: str,
        *,
        title: str,
        author: str,
        length: int,
        position: int = 0,
        uri: str,
        ytid: typing.Optional[str] = None,
        is_stream: bool,
        is_seekable: bool,
    ):
        self.id = id
        """Base64 track identifier given by lavalink."""

        self.author = author
        """Author of the track."""

        self.title = title
        """Title of the track."""

        self.length = length
        """Total length of the track."""

        self.position = position
        """Current position of the player on this track."""

        self.uri = uri
        """URI of the track."""

        self.ytid = ytid
        """Identifier of the track given by Youtube.

        This will be none if the track is not from Youtube."""

        self.is_stream = is_stream
        self.is_seekable = is_seekable

    @property
    def thumbnail(self) -> typing.Optional[str]:
        """Thumbnail of the track.

        Returns none if the track is not from Youtube"""
        if self.ytid:
            return f"https://img.youtube.com/vi/{self.ytid}/mqdefault.jpg"

    @classmethod
    def from_dict(cls, payload):
        info: dict[str, str] = payload["info"]
        return cls(
            payload["track"],  # base64 track identifier provided by lavalink
            author=info["author"],
            title=info["title"],
            length=info["length"],
            position=info["position"],
            uri=info["uri"],
            ytid=info.get("identifier", None),  # Identifier used by youtube
            is_stream=info["isStream"],
            is_seekable=info["isSeekable"],
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Track):
            raise TypeError(f"Expected {other} to type Track but got {type(other)}")
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


class SearchResult:
    def __init__(self, *, tracks: typing.Iterable[Track], query: str):
        self.tracks = tracks
        """Tracks returned by the query."""

        self.query = query
        """The query string."""


class YTPlaylist:
    def __init__(self, *, name: str, tracks: typing.Iterable[Track], selected_track: int):
        self.name = name
        """Name of the youtube playlist."""

        self.tracks = tracks
        """Tracks present in the Youtube playlist."""

        self.selected_track = selected_track
        """Current selected track."""

    def __len__(self) -> int:
        return len(self.tracks)
