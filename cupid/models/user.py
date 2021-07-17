"""Peewee ORM model for a user."""
from __future__ import annotations

import enum
from typing import Any

import peewee

from .database import BaseModel
from .enums import EnumField


class Gender(enum.Enum):
    """The gender of a user."""

    NON_BINARY = 'non_binary'
    FEMALE = 'female'
    MALE = 'male'


class User(BaseModel):
    """Peewee ORM model for a user."""

    id = peewee.BigIntegerField(primary_key=True)
    name = peewee.CharField(max_length=255)
    discriminator = peewee.FixedCharField(max_length=4)
    avatar_url = peewee.CharField(max_length=255)
    gender = EnumField(Gender, default=Gender.NON_BINARY)

    @classmethod
    def from_object(
            cls,
            obj: Any,
            id: int = None,
            gender: Gender = Gender.NON_BINARY) -> tuple[User, bool]:
        """Create or update a user from an object.

        The object must have `name`, `discriminator` and `avatar_url`
        attributes. The object may have an `id` attribute, otherwise the `id`
        parameter must  be passed. The object may have a `gender` attribute,
        otherwise the `gender` parameter will be used (or the current value,
        if the user is already registered).

        Returns the user and a boolean indicating if they were newly created.
        """
        id = getattr(obj, 'id', id)
        user = cls.get_or_none(cls.id == id)
        if user:
            user.name = obj.name
            user.discriminator = obj.discriminator
            user.avatar_url = obj.avatar_url
            user.gender = getattr(obj, 'gender', user.gender)
            user.save()
            return user, False
        return cls.create(
            id=id,
            name=obj.name,
            discriminator=obj.discriminator,
            avatar_url=obj.avatar_url,
            gender=getattr(obj, 'gender', gender),
        ), True

    def as_dict(self) -> dict[str, Any]:
        """Get the user as a dict for JSON serialisation."""
        return {
            'id': str(self.id),
            'name': self.name,
            'discriminator': self.discriminator,
            'avatar_url': self.avatar_url,
            'gender': self.gender.value,
        }
