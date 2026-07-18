from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base_class import Base

class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False)
    
    commit_hash: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # Statuses: "pending", "running", "completed", "failed"
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    
    error_message: Mapped[str] = mapped_column(String(500), nullable=True)
    
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    total_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    secrets_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Aggregate scores (e.g. 0 to 100, where 100 is secure)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    repository = relationship("Repository", back_populates="scans")
    branch = relationship("Branch", back_populates="scans")
    secrets = relationship("Secret", back_populates="scan", cascade="all, delete-orphan")
