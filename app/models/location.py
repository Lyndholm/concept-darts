import uuid

from sqlalchemy import TIMESTAMP, Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text

from ..controllers.database import Base


class Location(Base):
    __tablename__ = 'locations'

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String)
    world_id = Column(UUID(as_uuid=True), ForeignKey('worlds.id', ondelete='CASCADE'))
    creator_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'))

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

    image = Column(String, ForeignKey('files.filename', ondelete='CASCADE'), primary_key=True)
    name = Column(String)
    description = Column(String)
    location_id = Column(UUID(as_uuid=True), ForeignKey('locations.id', ondelete='CASCADE'), primary_key=True)

    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__}: '
            f'location_id={self.location_id!s} '
            f'image={self.name}'
            f'>'
        )

    __mapper_args__ = {'eager_defaults': True}
