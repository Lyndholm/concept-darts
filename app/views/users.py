from uuid import UUID

import sqlalchemy as sa
from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas, utils
from app.controllers import database, oauth2


router = APIRouter(
    prefix='/users',
    tags=['Users']
)


@router.get(
    '/me',
    response_model=schemas.UserOutPrivate,
    responses={
        401: {
            'model': schemas.ResponseError,
            'description': 'Unauthorized'
        },
    }
)
async def get_mine_user(
    db: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Returns the data of the authorized user"""

    # There is a bug which leads to AttributeError.
    # It may happen when user deletes their account
    # and then tries to request this endpoint
    try:
        query = await db.execute(sa.select(models.User).where(models.User.id == current_user.id))
        user = query.scalars().first()
    except AttributeError:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'status': 401, 'error': 'invalid credentials'},
            headers={'WWW-Authenticate': 'Bearer'}
        )

    return user


@router.get(
    '/',
    response_model=list[schemas.UserOutPublic]
)
async def get_all_users(
    db: AsyncSession = Depends(database.get_session),
    search: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
):
    """Returns a list of all users"""

    search = search if search else ''
    query = await db.execute(
        sa.select(models.User).
        where(sa.or_(
            models.User.first_name.contains(search),
            models.User.last_name.contains(search),
            models.User.additional_name.contains(search),
            models.User.username.contains(search)
            )
        ).
        limit(limit).
        offset(offset)
    )
    users = query.scalars().unique().all()
    return [schemas.UserOutPublic.from_orm(user) for user in users]


@router.get(
    '/{id}',
    response_model=schemas.UserOutPublic,
    responses={
        404: {
            'model': schemas.ResponseError,
            'description': 'The user was not found'
        },
    }
)
async def get_user(
    id: UUID,
    db: AsyncSession = Depends(database.get_session)
):
    """Returns the user with the specified id"""

    query = await db.execute(sa.select(models.User).where(models.User.id == id))
    user = query.scalars().first()

    if not user:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'status': 404, 'error': f'user with id={id!s} was not found'}
        )

    return schemas.UserOutPublic.from_orm(user)


@router.patch(
    '/me',
    response_model=schemas.UserUpdatedOut,
    responses={
        500: {
            'model': schemas.ResponseError,
            'description': 'Internal server error'
        },
    }
)
async def update_user(
    body: schemas.UserUpdate,
    db: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Updates the account of an authorized user"""

    try:
        if body.password is not None:
            hashed_password = utils.get_password_hash(body.password)
            body.password = hashed_password

        statement = (
            sa.update(models.User)
            .where(models.User.id == current_user.id)
            .values(**body.dict(exclude_unset=True))
            .returning(models.User)
        )
        query = (
            sa.select(models.User)
            .from_statement(statement)
            .execution_options(populate_existing=True)
        )
        data = await db.execute(query)
        await db.commit()

        updated_user = data.scalars().first()
        
        return schemas.UserUpdatedOut.from_orm(updated_user)

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
            'description': 'Forbidden to delete profile'
        },
        404: {
            'model': schemas.ResponseError,
            'description': 'The user was not found'
        },
        500: {
            'model': schemas.ResponseError,
            'description': 'Internal server error'
        },
    }
)
async def delete_user(
    id: UUID, 
    db: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Deletes the user with the specified id"""

    query = await db.execute(sa.select(models.User).where(models.User.id == id))

    if not query.scalars().first():
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'status': 404, 'error': f'user with id={id!s} was not found'}
        )

    if id != current_user.id:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={'status': 403, 'error': 'you can delete only your profile'}
        )

    try:
        await db.execute(sa.delete(models.User).where(models.User.id == id))
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
