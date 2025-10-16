from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "user"

    id_user = Column(Integer, primary_key=True, index=True)
    firstName = Column(String(100), nullable=False)
    lastName = Column(String(100), nullable=False)
    username = Column(String(100), nullable=False)
    phone = Column(String(20))
    id_status = Column(Boolean, default=True)

    # Relaciones
    user_roles = relationship("UserRole", back_populates="user")
    credentials = relationship("Credentials", back_populates="user")