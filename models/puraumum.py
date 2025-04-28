from pydantic import BaseModel, Field
from typing import List
from datetime import time

class PuraUmumData(BaseModel):
    _id: str
    nama_pura: str 
    description: str
    audio_decription: str
    image_pura: str
    virtual_path: List[str]
    status: str
    hariraya: str
    createdAt: str
    updatedAt: str