from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base_class import Base

class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # URL to clone the repo, e.g., HTTPS or SSH URL
    clone_url: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Provider: "github", "gitlab", "bitbucket", "local", "azure"
    provider: Mapped[str] = mapped_column(String(50), default="github", nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Access credentials (token/SSH key identifier) - stored safely or referenced
    access_token: Mapped[str] = mapped_column(String(255), nullable=True)
    
    last_synced_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    scan_schedule: Mapped[str] = mapped_column(String(50), default="manual", nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
 
    # Relationships
    user = relationship("User", back_populates="repositories")
    branches = relationship("Branch", back_populates="repository", cascade="all, delete-orphan")
    scans = relationship("Scan", back_populates="repository", cascade="all, delete-orphan")
    secrets = relationship("Secret", back_populates="repository", cascade="all, delete-orphan")


class Branch(Base):
    __tablename__ = "branches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    repository = relationship("Repository", back_populates="branches")
    scans = relationship("Scan", back_populates="branch", cascade="all, delete-orphan")
