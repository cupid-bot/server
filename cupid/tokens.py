"""Tools for parsing and serialising app and user tokens."""
from __future__ import annotations

import base64
import binascii
import dataclasses
import enum
from typing import Any

from . import models


class TokenParseError(ValueError):
    """An error encountered while parsing a token."""


class TokenType(enum.Enum):
    """The type of a token."""

    APP = 0
    SESSION = 1


@dataclasses.dataclass
class Token:
    """An authentication token.

    The first byte of a token (once decoded from base 64) indicates the token
    version. Currently, only version 0 is defined.

    In token version 0, the next byte indicates whether it is an app token
    (0), or a session token (1). The 4 bytes after that are a big endian
    integer, the ID of the app or session. The remaining bytes (the exact
    number is not defined) are the authentication secret.

    For example, the following is a session token with a 16 byte secret:

    00 01 00 00 02 6a 86 bc fd 6a e7 fb 46 1f 31 44 40 52 cb 1a 5f 2c

    Tokens will be encoded in a base 64 format (using '.' and '-' instead of
    '+' and '/', and no '=' padding).
    """

    version: int
    type: TokenType
    id: int
    secret: bytes

    @classmethod
    def from_entity(cls, entity: Any) -> Token:
        """Create a token for an app or session."""
        if isinstance(entity, models.App):
            type = TokenType.APP
        elif isinstance(entity, models.Session):
            type = TokenType.SESSION
        else:
            raise TypeError('Entity must be an app or session object.')
        return cls(version=0, type=type, id=entity.id, secret=entity.secret)

    @classmethod
    def from_token(cls, token: str) -> Token:
        """Parse a token."""
        # Add padding back.
        token += '=' * (4 - (len(token) % 4))
        try:
            data = base64.urlsafe_b64decode(token)
        except binascii.Error as e:
            raise TokenParseError('Invalid base 64.') from e
        if not token:
            raise TokenParseError('Token cannot be empty.')
        version = data[0]
        if version == 0:
            return cls.parse_version_0(data[1:])
        raise TokenParseError('Unkown token version.')

    @classmethod
    def parse_version_0(cls, data: bytes) -> Token:
        """Parse version 0 token data."""
        if len(data) < 6:
            raise TokenParseError('Token does not contain all fields.')
        type_value = data.pop(0)
        try:
            type = TokenParseError(type_value)
        except ValueError as e:
            raise TokenParseError('Invalid token type.') from e
        id = int.from_bytes(data[:4], 'big')
        secret = data[4:]
        return cls(version=0, type=type, id=id, secret=secret)

    def __str__(self) -> str:
        """Create the token from its fields."""
        if self.version == 0:
            data = self.serialise_version_0()
        else:
            raise ValueError('Unkown token version.')
        data = bytes([self.version, *data])
        return base64.urlsafe_b64encode(data).decode().rstrip('=')

    def serialise_version_0(self) -> list[int]:
        """Seriealise a version 0 token."""
        return [
            self.type.value,
            *self.id.to_bytes(4, 'big'),
            *bytearray(self.secret),
        ]

    def to_entity(self) -> Any:
        """Get the app or session for this token."""
        model = models.App if self.type == TokenType.APP else models.Session
        entity = model.get_or_none(
            model.id == self.id,
            model.secret == self.secret,
        )
        if not entity:
            raise TokenParseError('ID or secret is incorrect.')
        return entity
