__all__ = ("youganError", "AuthenticationError", "TrackLoadError")


class YouganError(RuntimeError):
    """Base class of all the errors raised by yougan."""


class AuthenticationError(YouganError):
    """Raised when invalid credentials are given."""

    node: str

    def __str__(self):
        return f"Invalid password provided for {self.node}"


class NodeAlreadyConnected(YouganError):
    """Raised when trying to connect to an already connected node."""

    node: str

    def __str__(self):
        return f"Node::{self.node} is already connected"


class TrackLoadError(YouganError):
    """Raised when a track fails to load"""

    error: str

    def __str__(self) -> str:
        return f"Track loading failed due to: {self.error}"
