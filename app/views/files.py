import uuid

import aiofiles
import sqlalchemy as sa
from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.controllers import database, oauth2

router = APIRouter(
    prefix='/files',
    tags=['Files']
)


@router.get(
    '/',
    response_model=list[schemas.FileOutWithStorageUrl]
)
async def get_all_files(
    db: AsyncSession = Depends(database.get_session),
    limit: int | None = None,
    offset: int | None = None,
):
    """Returns a list of all files"""

    query = await db.execute(
        sa.select(models.File).
        limit(limit).
        offset(offset)
    )
    files = query.scalars().unique().all()
    return [schemas.FileOutWithStorageUrl.from_orm(file) for file in files]


@router.post(
    '/upload',
    response_model=schemas.FileOut,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {
            'model': schemas.ResponseError,
            'description': 'Bad request. Unsupported file extension.'
        },
        500: {
            'model': schemas.ResponseError,
            'description': 'Internal server error'
        },
    }
)
async def upload_file(
    db: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(oauth2.get_current_user),   
    file: UploadFile = File(...)
):
    """Uploads file to the server"""

    allowed_content_type = ('image/png', 'image/jpg', 'image/jpeg')

    if file.content_type not in allowed_content_type:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                'status': 400,
                'error': 'unsupported file extension'
            }
        )

    filename = (uuid.uuid4().hex + '.' + file.filename.split('.')[-1]).lower()

    try:
        async with aiofiles.open(f'static/{filename}', 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)

        image_data = {
            'filename': filename, 
            'author_id': current_user.id
        }

        image = models.File(**image_data)
        db.add(image)
        await db.commit()
        return schemas.FileOut.from_orm(image)

    except Exception as e:
        await db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'status': 500,
                'error': f'something went wrong: {e}'
            }
        )
