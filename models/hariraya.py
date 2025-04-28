from pydantic import BaseModel, Field
from typing import List
from datetime import time

class HariRayaData(BaseModel):
    _id: str
    nama_hari_raya: str 
    description: str
    tanggal_mulai: str
    tanggal_berakhir: str
    status: str
    createdAt: str
    updatedAt: str