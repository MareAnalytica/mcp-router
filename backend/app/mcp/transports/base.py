import abc
import uuid
from typing import Any

from mcp import ClientSession


class BaseTransport(abc.ABC):
    def __init__(self, server_id: uuid.UUID, user_id: uuid.UUID):
        self.server_id = server_id
        self.user_id = user_id
        self._session: ClientSession | None = None

    @abc.abstractmethod
    async def connect(self, **kwargs: Any) -> ClientSession:
        """Establish connection and return an initialized ClientSession."""

    @abc.abstractmethod
    async def disconnect(self) -> None:
        """Tear down the connection cleanly."""

    @abc.abstractmethod
    def is_connected(self) -> bool:
        """Check if the transport is still connected."""

    @property
    def session(self) -> ClientSession | None:
        return self._session

    @property
    @abc.abstractmethod
    def transport_type(self) -> str:
        pass
