"""Routes for creating and managing relationships."""
import pydantic

from sanic.request import Request
from sanic.response import HTTPResponse, json

from .utils import (
    app,
    app_authenticated,
    get_relationship,
    get_user_by_id,
    parse_body,
)
from ..graph import check_relationship
from ..models import Relationship, RelationshipKind


class RelationshipForm(pydantic.BaseModel):
    """Form for creating a relationship proposal."""

    initiator: int
    other: int
    kind: RelationshipKind


@app.post('/relationships/new')
@app_authenticated
@parse_body(RelationshipForm)
async def propose_relationship(request: Request) -> HTTPResponse:
    """Create a new relationship proposal."""
    initiator = get_user_by_id(request.ctx.body.initiator)
    other = get_user_by_id(request.ctx.body.other)
    check_relationship(initiator, other, request.ctx.body.kind)
    return json(Relationship.create(
        initiator=initiator, other=other, kind=request.ctx.body.kind,
    ).as_json())


@app.post('/relationship/<id:int>/accept')
@app_authenticated
async def accept_relationship(request: Request, id: int) -> HTTPResponse:
    """Accept a relationship proposal."""
    rel = get_relationship(id)
    # Make sure circumstances have not changed since the proposal was created.
    check_relationship(rel.initiator, rel.other, rel.kind)
    rel.accepted = True
    rel.save()
    return json(rel.as_json())


@app.delete('/relationship/<id:int>')
@app_authenticated
async def leave_relationship(request: Request, id: int) -> HTTPResponse:
    """Leave or decline a relationship."""
    get_relationship(id).delete_instance()
    return HTTPResponse(status=204)
