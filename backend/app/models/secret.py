from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, func, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base_class import Base

class Secret(Base):
    __tablename__ = "secrets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    scan_id: Mapped[int] = mapped_column(Integer, ForeignKey("scans.id", ondelete="CASCADE"), nullable=False)
    repository_id: Mapped[int] = mapped_column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    column_number: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # E.g. "AWS Access Key", "OpenAI API Key", "Private Key", "Database URL"
    secret_type: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Store a SHA-256 hash or masked version of the secret to avoid database exposure of sensitive credentials
    detected_value_hashed: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Masked value like "AKIAIOSFODNN7XXXXXXX" for display in the UI
    masked_value: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Shannon entropy of the matched secret string
    entropy: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Statuses: "active", "resolved", "false_positive"
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    
    # Severities: "critical", "high", "medium", "low"
    severity: Mapped[str] = mapped_column(String(50), default="medium", nullable=False)
    
    # Lines surrounding the secret for developers to see where it is
    raw_context: Mapped[str] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    scan = relationship("Scan", back_populates="secrets")
    repository = relationship("Repository", back_populates="secrets")
    ai_analysis = relationship("AIAnalysis", back_populates="secret", uselist=False, cascade="all, delete-orphan")
