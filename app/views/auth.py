from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .. import oauth2
from ..database import get_session
from ..models import User
from ..schemas import ResponceError, Token, UserIn, UserOut
from ..utils import get_password_hash, verify_password

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


@router.post(
    '/login',
    response_model=Token,
    responses={
        401: {
            'model': ResponceError,
            'description': 'Invalid credentials'
        },
    }
)
async def login_user(
    credentials: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session)
):
    """Login for access token"""

    query = await db.execute(select(User).where(User.email == credentials.username))
    user = query.scalars().first()

    if not user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'status': 401, 'error': 'invalid credentials'},
            headers={'WWW-Authenticate': 'Bearer'}
        )

    if not verify_password(credentials.password, user.password):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'status': 401, 'error': 'invalid credentials'},
            headers={'WWW-Authenticate': 'Bearer'}
        )

    access_token = oauth2.create_access_token(data = {'user_id': user.id})

    return Token(access_token=access_token, token_type='bearer')
