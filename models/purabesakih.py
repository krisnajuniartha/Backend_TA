from pydantic import BaseModel, Field
from typing import List
from datetime import time

class PuraBesakihData(BaseModel):
    _id: str
    nama_pura: str 
    description: str
    audio_decription: str
    image_pura: str
    golongan_pura: str
    hariraya_id: List[str]
    status: str
    createdAt: str
    updatedAt: str