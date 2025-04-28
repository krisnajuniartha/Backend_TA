from pydantic import BaseModel
from typing import List

class Golongan(BaseModel):
    _id: str
    golongan: str