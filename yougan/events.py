from __future__ import annotations
import typing

from hikari.events import Event
from dataclasses import dataclass

if typing.TYPE_CHECKING:
    from hikari import traits
    from yougan.player import Player


class YouganEvent(Event):
    @property
    def app(self) -> traits.RESTAware:
        return self.app


@dataclass
class TrackStartEvent(YouganEvent):
    track: str
    player: Player
    app: traits.RESTAware


@dataclass
class TrackEndEvent(YouganEvent):
    track: str
    player: Player
    reason: str
    app: traits.RESTAware


@dataclass
class TrackStuckEvent(YouganEvent):
    track: str
    threshold: int
    player: Player
    app: traits.RESTAware


@dataclass
class TrackExceptionEvent(YouganEvent):
    track: str
    error: str
    player: Player
    app: traits.RESTAware
