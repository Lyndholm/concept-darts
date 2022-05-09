from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models import User
from ..schemas import ResponceError, UserIn, UserOut
from ..utils import get_password_hash

router = APIRouter(
    prefix='/auth',
    tags=['Auth']
)


@router.post(
    '/register',
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

    hashed_password = get_password_hash(body.password)
    body.password = hashed_password

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
