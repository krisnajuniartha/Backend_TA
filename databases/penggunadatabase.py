from models.pengguna import *
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
from email_validator import validate_email, EmailNotValidError
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
import time
from datetime import datetime
import re
import logging




uri = "mongodb+srv://krisnajuniartha:ffx9GWKjBMaQAuMm@tugas-akhir-database.ekayh.mongodb.net/?retryWrites=true&w=majority&appName=tugas-akhir-database"

client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=100000)
database = client["tugas_akhir_krisna"]

collection_pengguna = database["pengguna"]
collection_role =database["role"]
collection_status =database["status"]


try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)


async def get_role():
    role = []

    response = collection_role.find({})
    
    async for response_role in response:
        role_data = {
            "_id": str(response_role["_id"]),
            "role": response_role["role"],
            "default_status_id": response_role["default_status_id"]
        }
        role.append(role_data)

    return {"role_list": role}

async def get_status():
    status = []

    response = collection_status.find({})
    
    async for response_status in response:
        status_data = {
            "_id": str(response_status["_id"]),
            "status": response_status["status"]
        }
        status.append(status_data)

    return {"status_list": status}

async def get_user(email: str):

    # try:
    #     # Validasi email menggunakan email-validator
    #     valid = validate_email(email)
    # except EmailNotValidError as e:
    #     raise ValueError(f"Email tidak valid: {str(e)}")

    local_part, domain = email.split('@')

    user_dict = await collection_pengguna.find_one({
        "email": {
            "$regex": f"^{local_part}@{domain}$", 
            "$options": "i"
        }
    })

    print(user_dict)
    
    if user_dict:
        # Validasi dan konversi timestamps
        ts = user_dict.get("createdAt")
        if ts is not None:
            dt = datetime.fromtimestamp(ts)
            tanggal = dt.date()
            waktu = dt.time()
        else:
            dt, tanggal, waktu = None, None, None

        updateTs = user_dict.get("updatedAt")
        if updateTs is not None:
            updateDt = datetime.fromtimestamp(updateTs)
            updateTanggal = updateDt.date()
            updateWaktu = updateDt.time()
        else:
            updateDt, updateTanggal, updateWaktu = None, None, None

        user_dict["_id"] = str(user_dict["_id"])
        print(user_dict)
        user = UserInDB(
            _id=user_dict["_id"],
            nama=user_dict["nama"],
            email=user_dict["email"],
            foto_profile=user_dict["foto_profile"],
            password=user_dict["password"],
            test=user_dict["_id"],
            createdAtTime=str(waktu),
            createdAtDate=str(tanggal),
            updatedAtTime=str(updateWaktu),
            updatedAtDate=str(updateTanggal),
            role=user_dict["role_id"],
            status=user_dict["status_id"]
        )

        return user

    return None

async def fetch_one_user(id: str):
        object_id = ObjectId(id)
        
        document = await collection_pengguna.find_one({"_id": object_id})

        ts = document.get("createdAt")
        if ts is not None:
            dt = datetime.fromtimestamp(ts)
            tanggal = dt.date()
            waktu = dt.time()
        else:
            dt, tanggal, waktu = None, None, None

        updateTs = document.get("updatedAt")
        if updateTs is not None:
            updateDt = datetime.fromtimestamp(updateTs)
            updateTanggal = updateDt.date()
            updateWaktu = updateDt.time()
        else:
            updateDt, updateTanggal, updateWaktu = None, None, None
        
        user_data = {
            "_id": str(document["_id"]),
            "nama": document["nama"],
            "email": document["email"],
            "foto_profile": document["foto_profile"],
            "password": document["password"],
            "createdAt": dt,
            "createdDate": tanggal,
            "createdTime": waktu,
            "updatedAt": updateDt,
            "updatedDate": updateTanggal,
            "updateTime": updateWaktu,
            "role_id": document["role_id"],
            "status_id": document["status_id"]
        }

        return user_data

async def fetch_user_specific(email: str):
    local_part, domain = email.split('@')

    document = await collection_pengguna.find_one({"email": {"$regex": f"^{local_part}@{domain}$", 
            "$options": "i"
            }})
    
    return document

async def fetch_all_user_with_name(name: str):
    user = []
    cursor = collection_pengguna.find({"nama": {"$regex": f"(?i){name}"}})

    async for document in cursor:
        ts = document.get("createdAt")
        if ts is not None:
            dt = datetime.fromtimestamp(ts)
            tanggal = dt.date()
            waktu = dt.time()
        else:
            dt, tanggal, waktu = None, None, None

        updateTs = document.get("updatedAt")
        if updateTs is not None:
            updateDt = datetime.fromtimestamp(updateTs)
            updateTanggal = updateDt.date()
            updateWaktu = updateDt.time()
        else:
            updateDt, updateTanggal, updateWaktu = None, None, None
        
        user_data = {
            "_id": str(document["_id"]),
            "nama": document["nama"],
            "email": document["email"],
            "foto_profile": document["foto_profile"],
            "password": document["password"],
            "createdAt": dt,
            "createdDate": tanggal,
            "createdTime": waktu,
            "updatedAt": updateDt,
            "updatedDate": updateTanggal,
            "updateTime": updateWaktu,
            "role_id": document["role_id"],
            "status_id": document["status_id"]
        }
        user.append(user_data)
    
    return {"data_user": user}

async def fetch_all_user():
    user = []

    # Hanya ambil field yang diperlukan untuk meningkatkan efisiensi
    cursor = collection_pengguna.find({}, {
        "createdAt": 1,
        "updatedAt": 1,
        "nama": 1,
        "email": 1,
        "foto_profile": 1,
        "password": 1,
        "role_id": 1,
        "status_id": 1
    })

    async for document in cursor:
        # Validasi dan konversi timestamps
        ts = document.get("createdAt")
        if ts is not None:
            dt = datetime.fromtimestamp(ts)
            tanggal = dt.date()
            waktu = dt.time()
        else:
            dt, tanggal, waktu = None, None, None

        updateTs = document.get("updatedAt")
        if updateTs is not None:
            updateDt = datetime.fromtimestamp(updateTs)
            updateTanggal = updateDt.date()
            updateWaktu = updateDt.time()
        else:
            updateDt, updateTanggal, updateWaktu = None, None, None

        # Bangun data user dengan validasi setiap field
        user_data = {
            "_id": str(document["_id"]),
            "nama": document.get("nama", ""),
            "email": document.get("email", ""),
            "foto_profile": document.get("foto_profile", ""),
            "password": document.get("password", ""),
            "createdAt": dt,
            "createdDate": tanggal,
            "createdTime": waktu,
            "updatedAt": updateDt,
            "updatedDate": updateTanggal,
            "updateTime": updateWaktu,
            "role_id": document.get("role_id", []),
            "status_id": document.get("status_id", [])
        }

        user.append(user_data)

    return user


async def fetch_pengguna_by_filter(role: list[str], statusId: list[str]):
    user = []
    
    if statusId:
        statusId = [re.sub(r'^"|"$', '', status) for status in statusId]

    if role:
        role = [re.sub(r'^"|"$', '', roleData) for roleData in role]

    cursor = collection_pengguna.find({"status_id": {"$in": statusId}, "role_id": {"$in": role}})

    async for document in cursor:
        ts = document.get("createdAt")
        if ts is not None:
            dt = datetime.fromtimestamp(ts)
            tanggal = dt.date()
            waktu = dt.time()
        else:
            dt, tanggal, waktu = None, None, None

        updateTs = document.get("updatedAt")
        if updateTs is not None:
            updateDt = datetime.fromtimestamp(updateTs)
            updateTanggal = updateDt.date()
            updateWaktu = updateDt.time()
        else:
            updateDt, updateTanggal, updateWaktu = None, None, None

        user_data = {
            "_id": str(document["_id"]),
            "nama": document["nama"],
            "email": document["email"],
            "foto_profile": document["foto_profile"],
            "password": document["password"],
            "createdAt": dt,
            "createdDate": tanggal,
            "createdTime": waktu,
            "updatedAt": updateDt,
            "updatedDate": updateTanggal,
            "updateTime": updateWaktu,
            "role_id": document["role_id"],
            "status_id": document["status_id"]
        }

        user.append(user_data)
    
    return {"data_user": user}

async def create_user_data(nama: str, email: str, password: str, role_input:str):
    document: UserData
    role_data = await get_role()

    status_id: str = ""

    if role_data and "role_list" in role_data:
        for role_item in role_data["role_list"]:
            if role_item.get("_id") == role_input:
                status_id = role_item.get("default_status_id", "")
                break

    timestamps = time.time()

    document = {
        "nama": nama,
        "email": email,
        "foto_profile": "none",
        "password": password,
        "createdAt": timestamps,
        "updatedAt": timestamps,
        "status_id": status_id,
        "role_id": role_input 
    }


    result = await collection_pengguna.insert_one(document)
    
    return {"_id": str(result.inserted_id), "nama": nama, "message": "Data created successfully"}


async def create_ahli_data(nama: str, email: str, password: str):
    document: UserData

    timestamps = time.time()

    document = {
        "nama": nama,
        "email": email,
        "foto_profile": "none",
        "password": password,
        "createdAt": timestamps,
        "updatedAt": timestamps,
        "status_id": "reject",
        "role_id": "ahli gamelan bali" 
    }

    result = await collection_pengguna.insert_one(document)

    return {"_id": str(result.inserted_id), "nama": nama, "message": "Data created successfully"}

async def update_user_data(id: str, email: str, nama: str):
    object_id = ObjectId(id)

    update_data = {}

    timestamps = time.time()
    
    if nama:
        update_data["nama"] = nama

    if email:
        update_data["email"] = email

    if update_data:
        update_data["updatedAt"] = timestamps 

    print(update_data["nama"])
    print(update_data)

    await collection_pengguna.update_one(
        {"_id": object_id},
        {"$set": update_data},
    )
    
    return {"message": "Successfully Updated Data!", "updated_data": update_data}

async def update_user_photo(id: str, foto: str):
    object_id = ObjectId(id)
    
    updated_data = {}
    timestamps = time.time()

    if foto:
        updated_data["foto_profile"] = foto

    if updated_data:
        updated_data["updatedAt"] = timestamps

    await collection_pengguna.update_one({"_id": object_id}, {"$set": updated_data})

    document = await collection_pengguna.find_one({"_id": object_id})
    
    return document

async def delete_user_data(id: str):
    object_id = ObjectId(id)
    
    foto_profile = []

    cursor = collection_pengguna.find({"_id": object_id})

    async for document in cursor:
        foto_profile_data = document["foto_profile"]
    
        foto_profile.append(foto_profile_data)

    for path_todelete_foto in foto_profile:
        public_id = extract_public_id(path_todelete_foto)

        cloudinary.uploader.destroy(public_id)
    
    await collection_pengguna.delete_one({"_id": object_id})

    return True

def extract_public_id(secure_url):
    pattern = r"/upload/(?:v\d+/)?(.+)\.\w+$"
    match = re.search(pattern, secure_url)
    if match:
        return match.group(1)
    else:
        return None
    

async def approval_users_data(id: str, status: str):
    try:
        object_id = ObjectId(id)
    except Exception:
        raise ValueError("ID pengguna tidak valid")

    status_name: str = None
    timestamps = time.time()
    status_list = await get_status()
    if status_list and status_list["status_list"]:
        for status_data in status_list["status_list"]:
            if status_data.get("_id") == status:
                status_name = status_data.get("status", "")
                break

    update_response = await collection_pengguna.update_one(
        {"_id": object_id},
        {"$set": {"status_id": status, "updatedAt": timestamps}}
    )

    if update_response.modified_count > 0:
        return f"Status Pengguna berhasil diubah menjadi: {status_name}"
    else:
        return f"Gagal mengubah status Pengguna dengan ID: {id}"