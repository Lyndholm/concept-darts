from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models import User
from ..schemas import ResponceError, UserIn, UserOut, UserUpdate

router = APIRouter(
    prefix='/users',
    tags=['users']
)


@router.get(
    '/',
    response_model=list[UserOut]
)
async def get_all_users(db: AsyncSession = Depends(get_session)):
    """Get all users"""

    query = await db.execute(select(User))
    users = query.scalars().all()
    return [UserOut.from_orm(user) for user in users]


@router.get(
    '/{id}',
    response_model=UserOut,
    responses={
        404: {
            'model': ResponceError,
            'description': 'The user was not found'
        },
    }
)
async def get_user(id: int, db: AsyncSession = Depends(get_session)):
    """Get user by id"""

    query = await db.execute(select(User).where(User.id == id))
    user = query.scalars().first()

    if not user:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'status': 404, 'error': f'user with {id=} was not found'}
        )

    return UserOut.from_orm(user)


@router.post(
    '/',
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {
            'model': ResponceError,
            'description': 'A user with provided credentials is already registred'
        },
    }
)
async def create_user(body: UserIn, db: AsyncSession = Depends(get_session)):
    """Create new user"""

    # TODO: check if email is valid

    user = User(**body.dict())
    db.add(user)

    try:
        await db.commit()
        return UserOut.from_orm(user)
    except IntegrityError:
        await db.rollback()
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                'status': 409,
                'error': 'user with provided credentials is already registred'
            }
        )
    except:
        await db.rollback()


@router.patch(
    '/{id}',
    response_model=UserOut,
    responses={
        404: {
            'model': ResponceError,
            'description': 'The user was not found'
        },
    }
)
async def update_user(id: int, body: UserUpdate, db: AsyncSession = Depends(get_session)):
    """Update user data"""

    query = await db.execute(select(User).where(User.id == id))

    if not query.scalars().first():
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'status': 404, 'error': f'user with {id=} was not found'}
        )

    try:
        # TODO: if new password is in payload, need to hash it before storing in DB
        statement = update(User).where(User.id == id).values(**body.dict(exclude_unset=True)).returning(User)
        query = select(User).from_statement(statement).execution_options(populate_existing=True)
        data = await db.execute(query)
        await db.commit()

        updated_user = data.scalars().first()
        
        return UserOut.from_orm(updated_user)

    except Exception as e:
        await db.rollback()


@router.delete(
    '/{id}',
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {
            'model': ResponceError,
            'description': 'The user was not found'
        },
    }
)
async def delete_user(id: int, db: AsyncSession = Depends(get_session)):
    """Delete user"""

    query = await db.execute(select(User).where(User.id == id))

    if not query.scalars().first():
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'status': 404, 'error': f'user with {id=} was not found'}
        )

    try:
        await db.execute(delete(User).where(User.id == id))
        await db.commit()

        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        await db.rollback()
