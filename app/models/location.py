import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text

from app.controllers.database import Base


class Location(Base):
    __tablename__ = 'locations'

    id = sa.Column(UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4)
    name = sa.Column(sa.String, nullable=False)
    description = sa.Column(sa.String)
    world_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey('worlds.id', ondelete='CASCADE'))
    creator_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'))
    coord_x = sa.Column(sa.Float(precision=8), nullable=False)
    coord_y = sa.Column(sa.Float(precision=8), nullable=False)

    creator = relationship('User', lazy='joined')
    images = relationship('LocationImage', lazy='joined')

    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__}: '
            f'id={self.id} '
            f'name={self.name}'
            f'>'
        )

    __mapper_args__ = {'eager_defaults': True}


class LocationImage(Base):
    __tablename__ = 'locations_images'

    image = sa.Column(sa.String, sa.ForeignKey('files.filename', ondelete='CASCADE'), primary_key=True)
    name = sa.Column(sa.String)
    description = sa.Column(sa.String)
    location_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey('locations.id', ondelete='CASCADE'), primary_key=True)

    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__}: '
            f'location_id={self.location_id!s} '
            f'image={self.name}'
            f'>'
        )

    __mapper_args__ = {'eager_defaults': True}
