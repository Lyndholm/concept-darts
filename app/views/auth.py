import sqlalchemy as sa

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas, utils
from app.controllers import database, oauth2

router = APIRouter(
    prefix='/auth',
    tags=['Auth']
)


@router.post(
    '/register',
    response_model=schemas.UserCreated,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {
            'model': schemas.ResponseError,
            'description': 'A user with provided credentials is already registred'
        },
        500: {
            'model': schemas.ResponseError,
            'description': 'Internal server error'
        },
    }
)
async def create_user(
    body: schemas.UserIn,
    db: AsyncSession = Depends(database.get_session)
):
    """Creates a new user"""

    hashed_password = utils.get_password_hash(body.password)
    body.password = hashed_password

    user = models.User(**body.dict())
    db.add(user)

    try:
        await db.commit()
        return schemas.UserCreated.from_orm(user)
    except IntegrityError:
        await db.rollback()
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                'status': 409,
                'error': 'user with provided credentials is already registred'
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


@router.post(
    '/login',
    response_model=schemas.Token,
    responses={
        401: {
            'model': schemas.ResponseError,
            'description': 'Invalid credentials'
        },
    }
)
async def login_user(
    credentials: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(database.get_session)
):
    """Login for access token"""

    query = await db.execute(
        sa.select(models.User.id, models.User.password)
        .where(
            sa.or_(
                models.User.email == credentials.username,
                models.User.username == credentials.username
            )
        )
    )

    user = query.first()

    if not user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'status': 401, 'error': 'invalid credentials'},
            headers={'WWW-Authenticate': 'Bearer'}
        )

    if not utils.verify_password(credentials.password, user.password):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'status': 401, 'error': 'invalid credentials'},
            headers={'WWW-Authenticate': 'Bearer'}
        )

    access_token = oauth2.create_access_token(data = {'user_id': str(user.id)})

    return schemas.Token(access_token=access_token, token_type='bearer')
