from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..controllers import database, oauth2
from ..models import User
from ..schemas import ResponseError, UserOutPrivate, UserOutPublic, UserUpdate
from ..utils import get_password_hash

router = APIRouter(
    prefix='/users',
    tags=['Users']
)


@router.get(
    '/me',
    response_model=UserOutPrivate,
    responses={
        401: {
            'model': ResponseError,
            'description': 'Unauthorized'
        },
    }
)
async def get_mine_user(
    db: AsyncSession = Depends(database.get_session),
    current_user: User = Depends(oauth2.get_current_user)
):
    """Returns the data of the authorized user"""

    # There is a bug which leads to AttributeError.
    # It may happen when user deletes their account
    # and then tries to request this endpoint
    try:
        query = await db.execute(select(User).where(User.id == current_user.id))
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
    response_model=list[UserOutPublic]
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
        select(User).
        where(or_(
            User.first_name.contains(search),
            User.last_name.contains(search),
            User.username.contains(search)
            )
        ).
        limit(limit).
        offset(offset)
    )
    users = query.scalars().all()
    return [UserOutPublic.from_orm(user) for user in users]


@router.get(
    '/{id}',
    response_model=UserOutPublic,
    responses={
        404: {
            'model': ResponseError,
            'description': 'The user was not found'
        },
    }
)
async def get_user(
    id: UUID,
    db: AsyncSession = Depends(database.get_session)
):
    """Returns the user with the specified id"""

    query = await db.execute(select(User).where(User.id == id))
    user = query.scalars().first()

    if not user:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'status': 404, 'error': f'user with id={id!s} was not found'}
        )

    return UserOutPublic.from_orm(user)


@router.patch(
    '/{id}',
    response_model=UserOutPrivate,
    responses={
        403: {
            'model': ResponseError,
            'description': 'Forbidden to edit profile'
        },
        404: {
            'model': ResponseError,
            'description': 'The user was not found'
        },
        500: {
            'model': ResponseError,
            'description': 'Internal server error'
        },
    }
)
async def update_user(
    id: UUID,
    body: UserUpdate,
    db: AsyncSession = Depends(database.get_session),
    current_user: User = Depends(oauth2.get_current_user)
):
    """Updates the user data with the specified id"""

    query = await db.execute(select(User).where(User.id == id))

    if not query.scalars().first():
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'status': 404, 'error': f'user with id={id!s} was not found'}
        )

    if id != current_user.id:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={'status': 403, 'error': 'you can edit only your profile'}
        )

    try:
        if body.password is not None:
            hashed_password = get_password_hash(body.password)
            body.password = hashed_password

        statement = update(User).where(User.id == id).values(**body.dict(exclude_unset=True)).returning(User)
        query = select(User).from_statement(statement).execution_options(populate_existing=True)
        data = await db.execute(query)
        await db.commit()

        updated_user = data.scalars().first()
        
        return UserOutPrivate.from_orm(updated_user)

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
            'description': 'Forbidden to delete profile'
        },
        404: {
            'model': ResponseError,
            'description': 'The user was not found'
        },
        500: {
            'model': ResponseError,
            'description': 'Internal server error'
        },
    }
)
async def delete_user(
    id: UUID, 
    db: AsyncSession = Depends(database.get_session),
    current_user: User = Depends(oauth2.get_current_user)
):
    """Deletes the user with the specified id"""

    query = await db.execute(select(User).where(User.id == id))

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
        await db.execute(delete(User).where(User.id == id))
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
