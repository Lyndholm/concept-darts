from uuid import UUID

import sqlalchemy as sa

from fastapi import Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas


async def add_location_image_to_db(
    db: AsyncSession,
    location_id: UUID,
    image: schemas.LocationImageIn | dict
) -> Response | JSONResponse:
    """Adds an image to a specific location"""

    if type(image) is not dict:
        data = image.dict()
    else:
        data = image

    data.update({'location_id': location_id})

    insert_stmt = insert(models.LocationImage).values(**data)
    query = insert_stmt.on_conflict_do_nothing(index_elements=['image', 'location_id'])

    try:
        await db.execute(query)
        await db.commit()

        return Response(status_code=status.HTTP_201_CREATED)
    except sa.exc.IntegrityError:
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
