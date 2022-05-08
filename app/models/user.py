from sqlalchemy import Column, Integer, String, TIMESTAMP, DATE
from sqlalchemy.sql.expression import text

from ..database import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    additional_name = Column(String)
    date_of_birth = Column(DATE, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'))

    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__}('
            f'id={self.id}, '
            f'email={self.email}, '
            f')>'
        )
