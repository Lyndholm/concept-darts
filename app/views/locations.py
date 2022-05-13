from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..controllers import database, oauth2
from ..models import User, Location, World
from ..schemas import ResponseError, LocationIn, LocationOut, LocationUpdate

router = APIRouter(
    prefix='/locations',
    tags=['Locations']
)


@router.get(
    '/',
    response_model=list[LocationOut]
)
async def get_all_locations(
    db: AsyncSession = Depends(database.get_session),
    search: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
):
    """Returns a list of all locations"""

    search = search if search else ''
    query = await db.execute(
        select(Location).
        where(or_(
            Location.name.contains(search),
            Location.description.contains(search)
            )
        ).
        limit(limit).
        offset(offset)
    )
    locations = query.scalars().all()
    return [LocationOut.from_orm(location) for location in locations]


@router.get(
    '/{id}',
    response_model=LocationOut,
    responses={
        404: {
            'model': ResponseError,
            'description': 'The location was not found'
        },
    }
)
async def get_location(
    id: UUID,
    db: AsyncSession = Depends(database.get_session)
):
    """Returns the location with the specified id"""

    query = await db.execute(select(Location).where(Location.id == id))
    location = query.scalars().first()

    if not location:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'status': 404, 'error': f'location with id={id!s} was not found'}
        )

    return LocationOut.from_orm(location)


@router.post(
    '/',
    response_model=LocationOut,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {
            'model': ResponseError,
            'description': 'Unauthorized'
        },
        404: {
            'model': ResponseError,
            'description': 'World as a foreign key was not found'
        },
        500: {
            'model': ResponseError,
            'description': 'Internal server error'
        },
    }
)
async def create_location(
    body: LocationIn,
    db: AsyncSession = Depends(database.get_session),
    current_user: User = Depends(oauth2.get_current_user)
):
    """Creates a new location"""

    query = await db.execute(select(World).where(World.id == body.world_id))
    world = query.scalars().first()

    if not world:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'status': 404, 'error': f'world with id={body.world_id!s} was not found'}
        )

    body = body.dict()
    body.update({'creator_id': current_user.id})

    location = Location(**body)
    db.add(location)

    try:
        await db.commit()
        return LocationOut.from_orm(location)
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
    response_model=LocationOut,
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
            'description': 'The location was not found'
        },
        424: {
            'model': ResponseError,
            'description': 'The location does not have a creator, action can not be done'
        },
        500: {
            'model': ResponseError,
            'description': 'Internal server error'
        },
    }
)
async def update_location(
    id: UUID,
    body: LocationUpdate,
    db: AsyncSession = Depends(database.get_session),
    current_user: User = Depends(oauth2.get_current_user)
):
    """Updates the location data with the specified id"""

    # TODO: Make the function simple, there are many lines in it

    query = await db.execute(select(Location).where(Location.id == id))
    location = query.scalars().first()

    if not location:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'status': 404, 'error': f'location with id={id!s} was not found'}
        )

    if location.creator_id is not None:
        if location.creator_id != current_user.id:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={'status': 403, 'error': 'only location creator can edit the location'}
            )
    else:
        return JSONResponse(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            content={'status': 424, 'error': f'The location does not have a creator, so you can not edit it. Contact the support.'}
        )

    try:
        if body.creator_id is not None:
            query = await db.execute(select(User).where(User.id == body.creator_id))
            user = query.scalars().first()

            if not user:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={'status': 400, 'error': f'user with id={body.creator_id!s} does not exist'}
                )

        statement = update(Location).where(Location.id == id).values(**body.dict(exclude_unset=True)).returning(Location)
        query = select(Location).from_statement(statement).execution_options(populate_existing=True)
        data = await db.execute(query)
        await db.commit()

        updated_location = data.scalars().first()
        
        return LocationOut.from_orm(updated_location)
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
            'model': ResponseError,
            'description': 'Insufficient permissions to perform the action'
        },
        404: {
            'model': ResponseError,
            'description': 'The location was not found'
        },
        424: {
            'model': ResponseError,
            'description': 'The location does not have a creator, action can not be done'
        },
        500: {
            'model': ResponseError,
            'description': 'Internal server error'
        },
    }
)
async def delete_location(
    id: UUID, 
    db: AsyncSession = Depends(database.get_session),
    current_user: User = Depends(oauth2.get_current_user)
):
    """Deletes the location with the specified id"""

    query = await db.execute(select(Location).where(Location.id == id))
    location = query.scalars().first()

    if not location:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'status': 404, 'error': f'location with id={id!s} was not found'}
        )

    if location.creator_id is not None:
        if location.creator_id != current_user.id:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={'status': 403, 'error': 'only location creator can delete the location'}
            )
    else:
        return JSONResponse(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            content={'status': 424, 'error': 'The location does not have a creator, so you can not delete it. Contact the support.'}
        )

    try:
        await db.execute(delete(Location).where(Location.id == id))
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
