from typing import Any
from sqlalchemy.orm import DeclarativeBase, declared_attr

class Base(DeclarativeBase):
    id: Any
    __name__: str
    
    # Generate __tablename__ automatically based on class name in lowercase
    @declared_attr
    def __tablename__(cls) -> str:
        # Convert CamelCase to snake_case or simple lowercase. Let's use simple lowercase for table names
        # Or simple lower case. Since our models are User, Organization etc., user, organization works great.
        return cls.__name__.lower()
