from typing import List, Optional
from pydantic import BaseModel

class Person(BaseModel):
    id: str
    name: str
    birth: Optional[str] = None

class Relationship(BaseModel):
    start_id: str
    end_id: str
    type: str  # e.g. PARENT_OF, MARRIED

class GenealogicalTree(BaseModel):
    persons: List[Person]
    relationships: List[Relationship] 