from datetime import datetime
from sqlalchemy import Integer, DateTime, func, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base_class import Base

class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    secret_id: Mapped[int] = mapped_column(Integer, ForeignKey("secrets.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # AI generated content fields
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    remediation: Mapped[str] = mapped_column(Text, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    secret = relationship("Secret", back_populates="ai_analysis")
