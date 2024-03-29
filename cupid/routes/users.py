"""Routes for getting and managing users."""
import math
from typing import Optional

import peewee

import pydantic

from sanic.request import Request
from sanic.response import HTTPResponse, json

from .utils import (
    app,
    app_authenticated,
    authenticated,
    get_user_by_id,
    parse_args,
    parse_body,
    user_authenticated,
)
from ..graph import single_user_graph
from ..models import Gender, Relationship, User


class UserForm(pydantic.BaseModel):
    """Form for creating or updating a user."""

    name: pydantic.constr(min_length=1, max_length=255)
    avatar_url: pydantic.constr(min_length=7, max_length=255)
    gender: Gender
    discriminator: Optional[pydantic.constr(regex=r'^[0-9]{1,4}$')]  # noqa:F722,E501


class GenderUpdateForm(pydantic.BaseModel):
    """Form for changing a user's gender."""

    gender: Gender


class PaginationForm(pydantic.BaseModel):
    """Form for getting a paginated list of results."""

    search: Optional[str] = None
    per_page: int = 20
    page: int = 0


@app.get('/users/list')
@authenticated
@parse_args(PaginationForm)
async def list_users(request: Request) -> HTTPResponse:
    """Get a paginated list of users with associated data."""
    users = User.select()
    if search := request.ctx.args.search:
        users = users.where(User.name ** f'%{search}%')
    total = len(users)
    users = users.offset(request.ctx.args.page * request.ctx.args.per_page)
    users = users.limit(request.ctx.args.per_page)
    return json({
        'page': request.ctx.args.page,
        'per_page': request.ctx.args.per_page,
        'pages': math.ceil(total / request.ctx.args.per_page),
        'total': total,
        'users': [user.as_dict() for user in users],
    })


@app.get('/users/graph')
@authenticated
async def get_user_graph(request: Request) -> HTTPResponse:
    """Get a graph of all users and their relationships."""
    users = User.select().join(
        Relationship,
        peewee.JOIN.LEFT_OUTER,
        on=(
            (User.id == Relationship.initiator_id)
            | (User.id == Relationship.other_id)
        ) & (Relationship.accepted == True),    # noqa: E712
    ).where(Relationship.id.is_null(False)).group_by(User.id)
    user_data = {str(user.id): user.as_dict() for user in users}
    relationships = [
        rel.as_partial_dict() for rel in Relationship.select().where(
            Relationship.accepted == True,    # noqa: E712
        )
    ]
    return json({
        'users': user_data,
        'relationships': relationships,
    })


@app.put('/users/me/gender')
@user_authenticated
@parse_body(GenderUpdateForm)
async def update_own_gender(request: Request) -> HTTPResponse:
    """Update or register a user's details by ID."""
    request.ctx.user.gender = request.ctx.body.gender
    request.ctx.user.save()
    return json(request.ctx.user.as_dict())


@app.get('/user/<id:int>')
@authenticated
async def get_user(request: Request, id: int) -> HTTPResponse:
    """Get a user by ID."""
    user = get_user_by_id(id)
    accepted = Relationship.select().where(
        (
            (Relationship.initiator_id == id)
            | (Relationship.other_id == id)
        ),
        Relationship.accepted == True,    # noqa:E712
    )
    incoming = Relationship.select().where(
        Relationship.other_id == id,
        Relationship.accepted == False,    # noqa:E712
    )
    outgoing = Relationship.select().where(
        Relationship.initiator_id == id,
        Relationship.accepted == False,    # noqa:E712
    )
    return json({
        'user': user.as_dict(),
        'relationships': {
            'accepted': [rel.as_dict() for rel in accepted],
            'incoming': [rel.as_dict() for rel in incoming],
            'outgoing': [rel.as_dict() for rel in outgoing],
        },
    })


@app.get('/user/<id:int>/graph')
@authenticated
async def get_single_user_graph(request: Request, id: int) -> HTTPResponse:
    """Get a graph of all users related to one user."""
    get_user_by_id(id)
    user_ids = single_user_graph(id)
    users = {
        str(user.id): user.as_dict() for user in User.select()
        if user.id in user_ids
    }
    relationships = [
        rel.as_partial_dict() for rel in Relationship.select().where(
            Relationship.accepted == True,    # noqa: E712
            (
                (Relationship.initiator_id << user_ids)
                | (Relationship.other_id << user_ids)
            ),
        )
    ]
    return json({
        'users': users,
        'relationships': relationships,
    })


@app.put('/user/<id:int>')
@app_authenticated
@parse_body(UserForm)
async def update_user(request: Request, id: int) -> HTTPResponse:
    """Update or register a user's details by ID."""
    user, created = User.from_object(request.ctx.body, id=id)
    return json(user.as_dict(), 201 if created else 200)
