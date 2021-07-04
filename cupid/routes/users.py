"""Routes for getting and managing users."""
import math

import pydantic

from sanic.request import Request
from sanic.response import HTTPResponse, json

from .utils import (
    app,
    app_authenticated,
    authenticated,
    get_user_by_id,
    parse_body,
)
from ..models import Gender, Relationship, User


class UserForm(pydantic.BaseModel):
    """Form for creating or updating a user."""

    name: pydantic.constr(min_length=1, max_length=255)
    discriminator: pydantic.constr(regex=r'^[0-9]{4}$')    # noqa:F722
    avatar_url: pydantic.constr(min_length=6, max_length=255)
    gender: Gender


@app.get('/users/list')
@authenticated
async def list_users(request: Request) -> HTTPResponse:
    """Get a paginated list of users with associated data."""
    users = User.select()
    if search := request.args.get('search'):
        users = users.where(User.name ** f'%{search}%')
    per_page = request.args.get('per_page', 20)
    if page := request.args.get('page'):
        users = users.offset(page * per_page)
    users = users.limit(per_page)
    total = len(users)
    return json({
        'page': page,
        'per_page': per_page,
        'pages': math.ceil(total / per_page),
        'total': total,
        'users': [user.as_dict() for user in users],
    })


@app.get('/users/graph')
@authenticated
async def get_user_graph(request: Request) -> HTTPResponse:
    """Get a graph of all users and their relationships."""
    users = {str(user.id): user.as_dict() for user in User.select()}
    relationships = [
        {
            'initiator': rel.initiator.id,
            'other': rel.other.id,
            'kind': rel.other.value,
        } for rel in Relationship.select()
    ]
    return json({
        'users': users,
        'relationships': relationships,
    })


@app.get('/user/<id:int>')
@authenticated
async def get_user(request: Request, id: int) -> HTTPResponse:
    """Get a user by ID."""
    user = get_user_by_id(id)
    mutual = Relationship.select().where(
        Relationship.initiator_id == id,
        Relationship.other_id == id,
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
            'mutual': [rel.as_dict() for rel in mutual],
            'incoming': [rel.as_dict() for rel in incoming],
            'outgoing': [rel.as_dict() for rel in outgoing],
        },
    })


@app.put('/user/<id:int>')
@app_authenticated
@parse_body(UserForm)
async def update_user(request: Request, id: int) -> HTTPResponse:
    """Update or register a user's details by ID."""
    user = User.from_object(request.ctx.body, id=id)
    return json(user.as_dict())
