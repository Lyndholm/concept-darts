import uuid

from sqlalchemy import TIMESTAMP, Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text

from ..controllers.database import Base


class World(Base):
    __tablename__ = 'worlds'

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String)
    cover_image = Column(String)
    map_image = Column(String, nullable=False)
    creator_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'))

    creator = relationship('User', lazy='joined')

    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__}: '
            f'id={self.id!s} '
            f'name={self.name}'
            f'>'
        )

    __mapper_args__ = {'eager_defaults': True}
