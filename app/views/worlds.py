from uuid import UUID

import sqlalchemy as sa
from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.dialects.postgresql import insert as psql_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.controllers import database, oauth2


router = APIRouter(
    prefix='/worlds',
    tags=['Worlds']
)


@router.get(
    '/',
    response_model=list[schemas.WorldOut]
)
async def get_all_worlds(
    db: AsyncSession = Depends(database.get_session),
    search: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
):
    """Returns a list of all worlds"""

    search = search if search else ''
    query = await db.execute(
        sa.select(models.World)
        .where(sa.or_(
            models.World.name.contains(search),
            models.World.description.contains(search)
            )
        )
        .limit(limit)
        .offset(offset)
    )
    worlds = query.scalars().unique().all()
    return [schemas.WorldOut.from_orm(world) for world in worlds]


@router.get(
    '/{id}',
    response_model=schemas.WorldOut,
    responses={
        404: {
            'model': schemas.ResponseError,
            'description': 'The world was not found'
        },
    }
)
async def get_world(
    id: UUID,
    db: AsyncSession = Depends(database.get_session)
):
    """Returns the world with the specified id"""

    query = await db.execute(sa.select(models.World).where(models.World.id == id))
    world = query.scalars().first()

    if not world:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'status': 404, 'error': f'world with id={id!s} was not found'}
        )

    return schemas.WorldOut.from_orm(world)


@router.post(
    '/',
    response_model=schemas.WorldCreated,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {
            'model': schemas.ResponseError,
            'description': 'Unauthorized'
        },
        500: {
            'model': schemas.ResponseError,
            'description': 'Internal server error'
        },
    }
)
async def create_world(
    body: schemas.WorldIn,
    db: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Creates a new world"""

    body = body.dict()
    body.update({'creator_id': current_user.id})

    world = models.World(**body)
    db.add(world)

    try:
        await db.commit()
        return schemas.WorldCreated.from_orm(world)
    except Exception as e:
        await db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'status': 500,
                'error': f'something went wrong: {e}'
            }
        )


@router.patch(
    '/{id}',
    response_model=schemas.WorldCreated,
    responses={
        400: {
            'model': schemas.ResponseError,
            'description': 'Some of the body data is invalid'
        },
        403: {
            'model': schemas.ResponseError,
            'description': 'Forbidden to update one (or more) of the provided fields'
        },
        404: {
            'model': schemas.ResponseError,
            'description': 'The world was not found'
        },
        424: {
            'model': schemas.ResponseError,
            'description': 'The world does not have a creator, action can not be done'
        },
        500: {
            'model': schemas.ResponseError,
            'description': 'Internal server error'
        },
    }
)
async def update_world(
    id: UUID,
    body: schemas.WorldUpdate,
    db: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Updates the world data with the specified id"""

    # TODO: Make the function simple, there are many lines in it

    query = await db.execute(sa.select(models.World).where(models.World.id == id))
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
            query = await db.execute(sa.select(models.User).where(models.User.id == body.creator_id))
            user = query.scalars().first()

            if not user:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={'status': 400, 'error': f'user with id={body.creator_id!s} does not exist'}
                )

        statement = (
            sa.update(models.World)
            .where(models.World.id == id)
            .values(**body.dict(exclude_unset=True))
            .returning(models.World)
        )
        query = (
            sa.select(models.World)
            .from_statement(statement)
            .execution_options(populate_existing=True)
        )
        data = await db.execute(query)
        await db.commit()

        updated_world = data.scalars().first()
        
        return schemas.WorldCreated.from_orm(updated_world)
    except Exception as e:
        await db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'status': 500,
                'error': f'something went wrong: {e}'
            }
        )


@router.delete(
    '/{id}',
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        403: {
            'model': schemas.ResponseError,
            'description': 'Insufficient permissions to perform the action'
        },
        404: {
            'model': schemas.ResponseError,
            'description': 'The world was not found'
        },
        424: {
            'model': schemas.ResponseError,
            'description': 'The world does not have a creator, action can not be done'
        },
        500: {
            'model': schemas.ResponseError,
            'description': 'Internal server error'
        },
    }
)
async def delete_world(
    id: UUID, 
    db: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Deletes the world with the specified id"""

    query = await db.execute(sa.select(models.World).where(models.World.id == id))
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
        await db.execute(sa.delete(models.World).where(models.World.id == id))
        await db.commit()

        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        await db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'status': 500,
                'error': f'something went wrong: {e}'
            }
        )


@router.post(
    '/{id}/favourite',
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {
            'model': schemas.ResponseError,
            'description': 'Invalid data'
        },
        401: {
            'model': schemas.ResponseError,
            'description': 'Unauthorized'
        },
        500: {
            'model': schemas.ResponseError,
            'description': 'Internal server error'
        },
    }
)
async def favourite_world(
    id: UUID,
    db: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Adds a world to favorites"""

    insert_stmt = psql_insert(models.FavouriteWorld).values(world_id=id, user_id=current_user.id)
    query = insert_stmt.on_conflict_do_nothing(index_elements=['world_id', 'user_id'])

    try:
        await db.execute(query)
        await db.commit()

        return Response(status_code=status.HTTP_201_CREATED)
    except sa.exc.IntegrityError:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                'status': 400,
                'error': 'invalid world id'
            }
        )
    except Exception as e:
        await db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'status': 500,
                'error': f'something went wrong: {e}'
            }
        )


@router.delete(
    '/{id}/favourite',
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {
            'model': schemas.ResponseError,
            'description': 'Unauthorized'
        },
        500: {
            'model': schemas.ResponseError,
            'description': 'Internal server error'
        },
    }
)
async def unfavourite_world(
    id: UUID, 
    db: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Deletes a world from favourites"""

    try:
        await db.execute(
            sa.delete(models.FavouriteWorld)
            .where(
                sa.and_(
                models.FavouriteWorld.world_id == id,
                models.FavouriteWorld.user_id == current_user.id
                )
            )
        )
        await db.commit()

        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        await db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'status': 500,
                'error': f'something went wrong: {e}'
            }
        )
