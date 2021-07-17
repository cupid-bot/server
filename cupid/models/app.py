"""Peewee ORM model for an API app."""
import secrets
from typing import Any

import peewee

from .database import BaseModel
from .. import tokens


class App(BaseModel):
    """Peewee ORM model for a user authentication session."""

    name = peewee.CharField(max_length=255)
    secret = peewee.BlobField(default=secrets.token_bytes)

    @property
    def token(self) -> str:
        """Get this session's token."""
        return str(tokens.Token.from_entity(self))

    def as_dict(self, with_token: bool = False) -> dict[str, Any]:
        """Get the app as a dict for JSON serialisation."""
        return {
            'id': self.id,
            'name': self.name,
            **({'token': self.token} if with_token else {}),
        }
