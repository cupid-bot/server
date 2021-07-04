"""Peewee ORM model for a user authentication session."""
import secrets
from datetime import datetime
from typing import Any

import peewee

from .database import BaseModel, BytesField
from .user import User
from .. import tokens
from ..config import CONFIG


class Session(BaseModel):
    """Peewee ORM model for a user authentication session."""

    user = peewee.ForeignKeyField(User)
    secret = BytesField(default=secrets.token_bytes)
    created_at = peewee.DateTimeField(default=datetime.now)

    @property
    def token(self) -> str:
        """Get this session's token."""
        return str(tokens.Token.from_entity(self))

    def as_dict(self, with_token: bool = False) -> dict[str, Any]:
        """Get the session as a dict for JSON serialisation."""
        return {
            'id': self.id,
            'user': self.user.as_dict(),
            'expires_at': (
                self.created_at + CONFIG.session_expiry,
            ).timestamp(),
            **({'token': self.token} if with_token else {}),
        }
