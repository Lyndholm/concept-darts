from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models import User
from ..schemas import ResponceError, UserIn, UserOut

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

    result = await db.execute(select(User))
    users = result.scalars().all()
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

    result = await db.execute(select(User).where(User.id == id))
    user = result.scalars().first()

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
