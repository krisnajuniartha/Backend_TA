from pydantic import BaseModel
from typing import List

class Status(BaseModel):
    _id: str
    status: str