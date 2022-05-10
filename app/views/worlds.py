from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..controllers import database, oauth2
from ..models import User, World
from ..schemas import ResponseError, WorldIn, WorldOut, WorldUpdate

router = APIRouter(
    prefix='/worlds',
    tags=['Worlds']
)


@router.get(
    '/',
    response_model=list[WorldOut]
)
async def get_all_worlds(
    db: AsyncSession = Depends(database.get_session)
):
    """Returns a list of all worlds"""

    query = await db.execute(select(World))
    worlds = query.scalars().all()
    return [WorldOut.from_orm(world) for world in worlds]


@router.get(
    '/{id}',
    response_model=WorldOut,
    responses={
        404: {
            'model': ResponseError,
            'description': 'The world was not found'
        },
    }
)
async def get_world(
    id: UUID,
    db: AsyncSession = Depends(database.get_session)
):
    """Returns the world with the specified id"""

    query = await db.execute(select(World).where(World.id == id))
    world = query.scalars().first()

    if not world:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'status': 404, 'error': f'world with id={id!s} was not found'}
        )

    return WorldOut.from_orm(world)


@router.post(
    '/',
    response_model=WorldOut,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {
            'model': ResponseError,
            'description': 'Unauthorized'
        },
    }
)
async def create_world(
    body: WorldIn,
    db: AsyncSession = Depends(database.get_session),
    current_user: User = Depends(oauth2.get_current_user)
):
    """Creates a new world"""

    body = body.dict()
    body.update({'creator_id': current_user.id})

    world = World(**body)
    db.add(world)

    try:
        await db.commit()
        return WorldOut.from_orm(world)
    except:
        await db.rollback()


@router.patch(
    '/{id}',
    response_model=WorldOut,
    responses={
        400: {
            'model': ResponseError,
            'description': 'Some of the body data is invalid'
        },
        403: {
            'model': ResponseError,
            'description': 'Forbidden to update one (or more) of the provided fields'
        },
        404: {
            'model': ResponseError,
            'description': 'The world was not found'
        },
        424: {
            'model': ResponseError,
            'description': 'The world does not have a creator, action can not be done'
        },
    }
)
async def update_world(
    id: UUID,
    body: WorldUpdate,
    db: AsyncSession = Depends(database.get_session),
    current_user: User = Depends(oauth2.get_current_user)
):
    """Updates the world data with the specified id"""

    # TODO: Make the function simple, there are many lines in it

    query = await db.execute(select(World).where(World.id == id))
    world = query.scalars().first()

    if not world:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'status': 404, 'error': f'world with id={id!s} was not found'}
        )

    if world.creator_id is not None:
        if world.creator_id != current_user.id:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={'status': 403, 'error': 'only world creator can edit the world'}
            )
    else:
        return JSONResponse(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            content={'status': 424, 'error': f'The world does not have a creator, so you can not edit it. Contact the support.'}
        )

    try:
        if body.creator_id is not None:
            query = await db.execute(select(User).where(User.id == body.creator_id))
            user = query.scalars().first()

            if not user:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={'status': 400, 'error': f'user with id={body.creator_id} does not exist'}
                )

        statement = update(World).where(World.id == id).values(**body.dict(exclude_unset=True)).returning(World)
        query = select(World).from_statement(statement).execution_options(populate_existing=True)
        data = await db.execute(query)
        await db.commit()

        updated_world = data.scalars().first()
        
        return WorldOut.from_orm(updated_world)
    except:
        await db.rollback()


@router.delete(
    '/{id}',
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        403: {
            'model': ResponseError,
            'description': 'Insufficient permissions to perform the action'
        },
        404: {
            'model': ResponseError,
            'description': 'The world was not found'
        },
        424: {
            'model': ResponseError,
            'description': 'The world does not have a creator, action can not be done'
        },
    }
)
async def delete_world(
    id: UUID, 
    db: AsyncSession = Depends(database.get_session),
    current_user: User = Depends(oauth2.get_current_user)
):
    """Deletes the world with the specified id"""

    query = await db.execute(select(World).where(World.id == id))
    world = query.scalars().first()

    if not world:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'status': 404, 'error': f'world with id={id!s} was not found'}
        )

    if world.creator_id is not None:
        if world.creator_id != current_user.id:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={'status': 403, 'error': 'only world creator can delete the world'}
            )
    else:
        return JSONResponse(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            content={'status': 424, 'error': 'The world does not have a creator, so you can not delete it. Contact the support.'}
        )

    try:
        await db.execute(delete(World).where(World.id == id))
        await db.commit()

        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        await db.rollback()