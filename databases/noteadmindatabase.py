# from models. import *
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder
import json
from fastapi import FastAPI, HTTPException
import re
import time
from datetime import datetime
from typing import List

uri = "mongodb+srv://krisnajuniartha:ffx9GWKjBMaQAuMm@tugas-akhir-database.ekayh.mongodb.net/?retryWrites=true&w=majority&appName=tugas-akhir-database"

client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=10000)
database = client["tugas_akhir_krisna"]

collectionNode = database["note-admin"]

async def getNote(id: str):
    response = await collectionNode.find_one({"id_data": id})

    if response:
        dataInsert = {
            "_id": str(response["_id"]),
            "note": response["note"],
            "id_data": response["id_data"],
            "id_status": response["id_status"]
        }
        return dataInsert
    return None  # Tambahkan return None jika tidak ditemukan

async def createNote(note: str, idData: str, idStatus: str):
    if note and idData and idStatus:
        dataNote = {
            "note": note,
            "id_data": idData,
            "id_status": idStatus
        }

        response = await collectionNode.insert_one(dataNote)

        if response.inserted_id:
            return {"_id": str(response.inserted_id), "status": "Successfully added note!"}
    return None  # Tambahkan return None jika gagal

async def updateNote(idData: str, note: str = None, idStatus: str = None):
    updatedData = {}

    if note:
        updatedData["note"] = note

    if idStatus:
        updatedData["id_status"] = idStatus

    response = await collectionNode.update_one({"id_data": idData}, {"$set": updatedData})

    if response.modified_count > 0:  # Periksa modified_count
        return {"message": "Data updated successfully", "updated_data": updatedData}
    return None  # Tambahkan return None jika tidak ada yang diupdate

async def deleteNote(id: str):
    responseDelete = await collectionNode.delete_one({"id_data": id})
    if responseDelete.deleted_count > 0:  # Periksa deleted_count
        return True
    return False  # Tambahkan return False jika gagal