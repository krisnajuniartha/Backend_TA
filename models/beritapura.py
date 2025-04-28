from pydantic import BaseModel, Field
from typing import List
from datetime import time

class BeritaPuraData(BaseModel):
    _id: str
    judul_berita: str 
    description: str
    foto_berita: str
    status: str
    createdAt: str
    updatedAt: str