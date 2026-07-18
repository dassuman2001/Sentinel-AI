from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings

# Create SQLAlchemy engine with pool configurations suitable for web apps
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # checks connection health before using
    pool_size=10,        # maximum number of persistent connections
    max_overflow=20     # maximum overflow connections
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
