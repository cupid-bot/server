"""Tools which involve analysing the relationship graph."""
import logging

from peewee import Expression, JOIN, fn

from .models import Relationship, RelationshipKind, User


logger = logging.getLogger('cupid')


class RelationshipForbidden(ValueError):
    """An exception indicating that a relationship is not allowed."""


def array_agg(expr: Expression) -> Expression:
    """Do array aggregation and instruct Peewee not to coerce."""
    return fn.ARRAY_AGG(expr, coerce=False)


def get_connections() -> dict[int, set[int]]:
    """Get a map of all relationships each user has."""
    Related = User.alias('related')
    self_initiator = Relationship.initiator_id == User.id
    them_initiator = Relationship.initiator_id == Related.id
    self_other = Relationship.other_id == User.id
    them_other = Relationship.other_id == Related.id
    users = User.select(
        User, array_agg(Related.id).alias('relations'),
    ).join(
        Relationship, JOIN.LEFT_OUTER, self_initiator | self_other,
    ).join(
        Related,
        JOIN.LEFT_OUTER,
        (self_initiator & them_other) | (self_other & them_initiator),
    ).where(Relationship.accepted == True).group_by(User.id)    # noqa:E712
    return {user.id: set(user.relations) for user in users}


def distance(user_1: User, user_2: User) -> int:
    """Determine how closely two users are related.

    0 means they are the same user, -1 means they are not related.
    """
    logger.debug(f'Getting distance between {user_1.id} and {user_2.id}.')
    visited = {user_1.id}
    expanded = set()
    distance = 0
    connections = get_connections()
    logger.debug(f'Got {connections=}.')
    while True:
        reached_end = True
        for node in visited - expanded:
            if node == user_2.id:
                logger.debug(f'Found user 2 at {distance=}.')
                return distance
            visited |= connections.get(node, set())
            expanded.add(node)
            reached_end = False
        if reached_end:
            logger.debug('Users are not related.')
            return -1
        distance += 1
        logger.debug(f'{distance=}, {visited=}, {expanded=}')


def either_married(user_1: User, user_2: User) -> bool:
    """Check if either of two users are married."""
    return bool(Relationship.get_or_none(
        (
            (Relationship.initiator_id == user_1.id)
            | (Relationship.initiator_id == user_2.id)
            | (Relationship.other_id == user_1.id)
            | (Relationship.other_id == user_2.id)
        ) & (Relationship.kind == RelationshipKind.MARRIAGE)
        & (Relationship.accepted == True),    # noqa:E712
    ))


def is_adopted(user: User) -> bool:
    """Check if a user has a parent."""
    return bool(Relationship.get_or_none(
        Relationship.other_id == user.id,
        Relationship.accepted == True,    # noqa:E712
        Relationship.kind == RelationshipKind.ADOPTION,
    ))


def check_relationship(initiator: User, other: User, kind: RelationshipKind):
    """Make sure that a relationship is allowed."""
    if distance(initiator, other) != -1:
        raise RelationshipForbidden(
            'You cannot create a relationship with someone you are already '
            'related to.',
        )
    if kind == RelationshipKind.MARRIAGE:
        if either_married(initiator, other):
            raise RelationshipForbidden('A user cannot marry twice.')
    elif kind == RelationshipKind.ADOPTION:
        if is_adopted(other):
            raise RelationshipForbidden('A user can only be adopted once.')
