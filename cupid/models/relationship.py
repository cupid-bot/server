"""Peewee ORM model for a relationship between two users."""
import enum
from datetime import datetime
from typing import Any

import peewee

from .database import BaseModel
from .enums import EnumField
from .user import User


class RelationshipKind(enum.Enum):
    """The type of a relationship."""

    MARRIAGE = 'marriage'
    ADOPTION = 'adoption'


class Relationship(BaseModel):
    """Peewee ORM model for a relationship between two users."""

    initiator = peewee.ForeignKeyField(User)
    other = peewee.ForeignKeyField(User)
    accepted = peewee.BooleanField(default=False)
    kind = EnumField(RelationshipKind)
    created_at = peewee.DateTimeField(default=datetime.now)
    accepted_at = peewee.DateTimeField(null=True)

    def as_dict(self) -> dict[str, Any]:
        """Get the relationship as a dict for JSON serialisation."""
        return {
            'id': self.id,
            'initiator': self.initiator.as_dict(),
            'other': self.other.as_dict(),
            'accepted': self.accepted,
            'kind': self.kind.value,
            'created_at': self.created_at.timestamp(),
            'accepted_at': (
                self.accepted_at.timestamp() if self.accepted_at else None
            ),
        }

    def as_partial_dict(self) -> dict[str, Any]:
        """Get the relationship as a dict with minimal information."""
        return {
            'id': self.id,
            'initiator': str(self.initiator.id),
            'other': str(self.other.id),
            'kind': self.kind.value,
            'created_at': self.created_at.timestamp(),
            'accepted_at': self.accepted_at.timestamp(),
        }
