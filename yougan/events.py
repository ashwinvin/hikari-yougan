from __future__ import annotations
import typing

from hikari.events import Event

if typing.TYPE_CHECKING:
    from hikari import traits
    from yougan.player import Player


class YouganEvent(Event):
    @property
    def app(self) -> traits.RESTAware:
        return self.app

    @app.setter
    def set_app(self, app):
        self.app = app


class TrackStartEvent(YouganEvent):
    def __init__(self, *, track: str, player: Player, app: traits.RESTAware) -> None:
        super().__init__()
        self.track = track
        self.player = player


class TrackEndEvent(YouganEvent):
    def __init__(self, *, track: str, reason: str, player: Player, app: traits.RESTAware) -> None:
        super().__init__()
        self.track = track
        self.reason = reason
        self.player = player


class TrackStuckEvent(YouganEvent):
    def __init__(self, *, track: str, threshold: int, player: Player, app: traits.RESTAware) -> None:
        super().__init__()
        self.track = track
        self.threshold = threshold
        self.player = player


class TrackExceptionEvent(YouganEvent):
    def __init__(self, *, track: str, error: str, player: Player, app: traits.RESTAware) -> None:
        super().__init__()
        self.track = track
        self.error = error
        self.player = player
