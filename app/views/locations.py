from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import and_, delete, or_, select, update, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas, controllers
from ..controllers import database, oauth2

router = APIRouter(
    prefix='/locations',
    tags=['Locations']
)


@router.get(
    '/',
    response_model=list[schemas.LocationOut]
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
        select(models.Location).
        where(or_(
            models.Location.name.contains(search),
            models.Location.description.contains(search)
            )
        ).
        limit(limit).
        offset(offset)
    )
    locations = query.scalars().unique().all()
    return [schemas.LocationOut.from_orm(location) for location in locations]


@router.get(
    '/{id}',
    response_model=schemas.LocationOut,
    responses={
        404: {
            'model': schemas.ResponseError,
            'description': 'The location was not found'
        },
    }
)
async def get_location(
    id: UUID,
    db: AsyncSession = Depends(database.get_session)
):
    """Returns the location with the specified id"""

    query = await db.execute(select(models.Location).where(models.Location.id == id))
    location = query.scalars().first()

    if not location:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'status': 404, 'error': f'location with id={id!s} was not found'}
        )

    return schemas.LocationOut.from_orm(location)


@router.post(
    '/',
    response_model=schemas.LocationCreated,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {
            'model': schemas.ResponseError,
            'description': 'Unauthorized'
        },
        404: {
            'model': schemas.ResponseError,
            'description': 'World as a foreign key was not found'
        },
        500: {
            'model': schemas.ResponseError,
            'description': 'Internal server error'
        },
    }
)
async def create_location(
    body: schemas.LocationIn,
    db: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Creates a new location"""

    query = await db.execute(select(models.World).where(models.World.id == body.world_id))
    world = query.scalars().first()

    if not world:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'status': 404, 'error': f'world with id={body.world_id!s} was not found'}
        )

    body = body.dict()
    body.update({'creator_id': current_user.id})
    images = body.pop('images')

    insert_stmt = insert(models.Location).values(**body).returning(models.Location)
    query = select(models.Location).from_statement(insert_stmt).execution_options(populate_existing=True)

    try:
        data = await db.execute(query)
        await db.commit()
        location = data.scalars().first()

    except Exception as e:
        await db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'status': 500,
                'error': f'something went wrong: {e}'
            }
        )

    for image in images:
        await controllers.add_location_image_to_db(db, location.id, image)

    return schemas.LocationCreated.from_orm(location)


@router.patch(
    '/{id}',
    response_model=schemas.LocationOut,
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
            'description': 'The location was not found'
        },
        424: {
            'model': schemas.ResponseError,
            'description': 'The location does not have a creator, action can not be done'
        },
        500: {
            'model': schemas.ResponseError,
            'description': 'Internal server error'
        },
    }
)
async def update_location(
    id: UUID,
    body: schemas.LocationUpdate,
    db: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Updates the location data with the specified id"""

    # TODO: Make the function simple, there are many lines in it

    query = await db.execute(select(models.Location).where(models.Location.id == id))
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
            query = await db.execute(select(models.User).where(models.User.id == body.creator_id))
            user = query.scalars().first()

            if not user:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={'status': 400, 'error': f'user with id={body.creator_id!s} does not exist'}
                )

        statement = update(models.Location).where(models.Location.id == id).values(**body.dict(exclude_unset=True)).returning(models.Location)
        query = select(models.Location).from_statement(statement).execution_options(populate_existing=True)
        data = await db.execute(query)
        await db.commit()

        updated_location = data.scalars().first()
        
        return schemas.LocationOut.from_orm(updated_location)
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
            'description': 'The location was not found'
        },
        424: {
            'model': schemas.ResponseError,
            'description': 'The location does not have a creator, action can not be done'
        },
        500: {
            'model': schemas.ResponseError,
            'description': 'Internal server error'
        },
    }
)
async def delete_location(
    id: UUID, 
    db: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Deletes the location with the specified id"""

    query = await db.execute(select(models.Location).where(models.Location.id == id))
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
        await db.execute(delete(models.Location).where(models.Location.id == id))
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


@router.get(
    '/{id}/images',
    response_model=list[schemas.LocationImageOut]
)
async def get_location_images(
    id: UUID,
    db: AsyncSession = Depends(database.get_session)
):
    """Returns a list of images for a specific location"""

    query = await db.execute(select(models.LocationImage).where(models.LocationImage.location_id == id))
    images = query.scalars().all()

    return [schemas.LocationImageOut.from_orm(img) for img in images]


@router.post(
    '/{id}/images',
    responses={
        400: {
            'model': schemas.ResponseError,
            'description': 'Invalid data'
        },
        500: {
            'model': schemas.ResponseError,
            'description': 'Internal server error'
        },
    }
)
async def add_location_image(
    id: UUID,
    image: schemas.LocationImageIn,
    db: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Adds an image to a specific location"""

    return await controllers.add_location_image_to_db(db, id, image)


@router.delete(
    '/{id}/images',
    responses={
        400: {
            'model': schemas.ResponseError,
            'description': 'Invalid data'
        },
        500: {
            'model': schemas.ResponseError,
            'description': 'Internal server error'
        },
    }
)
async def delete_location_image(
    id: UUID,
    image: str,
    db: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Deletes an image from a location"""

    try:
        await db.execute(
            delete(models.LocationImage)
            .where(
                and_(
                    models.LocationImage.image == image,
                    models.LocationImage.location_id == id
                ) 
            )
        )
        await db.commit()
    except IntegrityError:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                'status': 400,
                'error': 'invalid image or location id'
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

    return Response(status_code=status.HTTP_204_NO_CONTENT)
