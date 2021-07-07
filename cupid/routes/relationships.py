"""Routes for creating and managing relationships."""
import pydantic

from sanic.exceptions import SanicException
from sanic.request import Request
from sanic.response import HTTPResponse, json

from .utils import (
    app,
    get_relationship,
    get_relationship_or_none,
    get_user_by_id,
    parse_body,
    user_authenticated,
)
from ..graph import RelationshipForbidden, check_relationship
from ..models import Relationship, RelationshipKind


class RelationshipForm(pydantic.BaseModel):
    """Form for creating a relationship proposal."""

    kind: RelationshipKind


@app.post('/user/<id:int>/relationship')
@parse_body(RelationshipForm)
@user_authenticated
async def propose_relationship(request: Request, id: int) -> HTTPResponse:
    """Create a new relationship proposal."""
    if get_relationship_or_none(request.ctx.user.id, id):
        raise RelationshipForbidden(
            'You cannot have multiple relationships with one user.',
        )
    initiator = request.ctx.user
    other = get_user_by_id(id)
    check_relationship(initiator, other, request.ctx.body.kind)
    return json(Relationship.create(
        initiator=initiator, other=other, kind=request.ctx.body.kind,
    ).as_json(), 201)


@app.get('/user/<id:int>/relationship')
@user_authenticated
async def get_own_relationship(request: Request, id: int) -> HTTPResponse:
    """Get your relationship with a user."""
    return json(get_relationship(request.ctx.user.id, id).as_json())


@app.post('/user/<id:int>/relationship/accept')
@user_authenticated
async def accept_relationship(request: Request, id: int) -> HTTPResponse:
    """Accept a relationship proposal."""
    rel = get_relationship(request.ctx.user.id, id)
    if rel.accepted:
        raise SanicException('Relationship already accepted.', 409)
    # Make sure circumstances have not changed since the proposal was created.
    check_relationship(rel.initiator, rel.other, rel.kind)
    rel.accepted = True
    rel.save()
    return json(rel.as_json())


@app.delete('/user/<id:int>/relationship')
@user_authenticated
async def leave_relationship(request: Request, id: int) -> HTTPResponse:
    """Leave or decline a relationship."""
    get_relationship(request.ctx.user.id, id).delete_instance()
    return HTTPResponse(status=204)
